import json
import os
import logging
import time
from typing import List, Dict, Any, Optional
from app.core.database import supabase
from app.core.ai import generate_embeddings
from app.core.config import logger
import asyncio
from app.models.schemas import ParserOutput

class PDFEmbedder:
    """Class for embedding PDF chunks into vector database"""
    
    def __init__(self, chunked_json_path: str = None):
        """Initialize the PDF embedder with chunked JSON file path"""
        self.chunked_json_path = chunked_json_path
    
    def load_json(self, file_path: str = None) -> Dict[str, Any]:
        """Load JSON data from a file."""
        file_path = file_path or self.chunked_json_path
        logger.info(f"Loading JSON from {file_path}")
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data
    
    def embed_chunks(self, chunks: List[Dict[str, Any]], project_id: int = None, document_id: str = None, user_id: str = None) -> List[Dict[str, Any]]:
        """Generate embeddings for chunks and prepare for database insertion"""
        logger.info(f"Generating embeddings for {len(chunks)} chunks")
        
        # Generate a timestamp for unique IDs
        timestamp = int(time.time())
        
        # Create a single source_id for all chunks from this document
        source_id = f"source_{document_id or 'unknown'}_{timestamp}"
        
        embedded_chunks = []
        for i, chunk in enumerate(chunks):
            # Generate embedding using the AI service
            embedding = generate_embeddings(chunk["text"])
            
            # Prepare record for database - ensure we use column names that exist in the schema
            record = {
                "source_id": source_id,  # Same source_id for all chunks from this document
                "chunk_id": f"{document_id or 'doc'}_{timestamp}_{i}",  # Unique chunk_id for each chunk
                "raw_text": chunk["text"],
                "embedding": embedding,
                "metadata": chunk["metadata"] or {},
            }
            
            # Add project_id if provided - both at root level and in metadata
            if project_id is not None:
                try:
                    # Convert to integer if it's not already
                    project_id_int = int(project_id)
                    record["project_id"] = project_id_int
                    record["metadata"]["project_id"] = project_id_int
                    logger.info(f"Adding project_id={project_id_int} to chunk {i+1}/{len(chunks)}")
                except (ValueError, TypeError) as e:
                    logger.error(f"Error converting project_id to int: {e}")
                    logger.info(f"Using original project_id={project_id} without conversion")
                    record["project_id"] = project_id
                    record["metadata"]["project_id"] = project_id
            else:
                logger.warning(f"No project_id provided for chunk {i+1}/{len(chunks)}")
                
            # Add document_id if provided
            if document_id:
                record["metadata"]["document_id"] = document_id
                
            # Add user_id if provided
            if user_id:
                record["metadata"]["user_id"] = user_id
            
            embedded_chunks.append(record)
            
            # Log progress for large documents
            if (i + 1) % 10 == 0:
                logger.info(f"Embedded {i + 1}/{len(chunks)} chunks")
        
        return embedded_chunks
    
    def insert_into_supabase(self, embedded_chunks: List[Dict[str, Any]], table_name: str = "sources") -> bool:
        """Insert embedded chunks into Supabase"""
        logger.info(f"Inserting {len(embedded_chunks)} chunks into Supabase table: {table_name}")
        
        try:
            # Insert in batches to avoid request size limitations
            batch_size = 50
            for i in range(0, len(embedded_chunks), batch_size):
                batch = embedded_chunks[i:i + batch_size]
                
                # Log the first chunk to debug what's being sent to Supabase
                if i == 0:
                    example_chunk = batch[0]
                    logger.info(f"Example chunk being sent to Supabase (first 200 chars of text): {example_chunk.get('raw_text', '')[:200]}")
                    logger.info(f"Example chunk project_id: {example_chunk.get('project_id')}")
                    logger.info(f"Example chunk metadata: {example_chunk.get('metadata')}")
                
                # CRITICAL FIX: Always include "project_id" in the list of columns to upsert
                # Construct a complete list of columns based on the first chunk
                columns = ["chunk_id", "metadata", "source_id", "embedding", "raw_text"]
                # Add project_id column if any chunk has it
                if any(chunk.get('project_id') is not None for chunk in batch):
                    columns.append("project_id")
                    logger.info(f"Including project_id in columns list: {columns}")
                
                # Use upsert with explicit columns and chunk_id as the conflict resolution key
                response = supabase.table(table_name).upsert(
                    batch, 
                    on_conflict="chunk_id",
                    returning="minimal"  # Minimize response size
                ).execute()
                
                # Check if the response has the expected structure
                # In newer versions of supabase-py, the structure might be different
                if not hasattr(response, 'data'):
                    logger.error(f"Failed to insert batch {i//batch_size + 1}: unexpected response structure")
                    logger.error(f"Response: {response}")
                    return False
                
                # Check if data is None or empty (indicating an error)
                if response.data is None or len(response.data) == 0:
                    logger.error(f"Failed to insert batch {i//batch_size + 1}: empty response data")
                    return False
                
                logger.info(f"Inserted batch {i//batch_size + 1}/{(len(embedded_chunks)-1)//batch_size + 1}")
            
            logger.info(f"Successfully inserted all {len(embedded_chunks)} chunks")
            return True
            
        except Exception as e:
            logger.error(f"Error inserting chunks into Supabase: {str(e)}")
            return False
    
    def process(self, project_id: Optional[int] = None, document_id: Optional[str] = None, user_id: Optional[str] = None) -> bool:
        """
        Process the chunks by generating embeddings and storing in database
        
        Args:
            project_id: Optional project ID to associate with the sources
            document_id: Optional document ID to include in metadata
            user_id: Optional user ID to associate with the sources
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            logger.info(f"Processing chunks with project_id={project_id}, document_id={document_id}")
            
            # Read the chunked data
            with open(self.chunked_json_path, 'r', encoding='utf-8') as f:
                chunks_data = json.load(f)
            
            # Get chunks directly from the 'chunks' field without validation
            chunks = chunks_data.get('chunks', [])
            if not chunks:
                logger.warning(f"No chunks found in {self.chunked_json_path}")
                return False
                
            # Generate embeddings for the chunks
            embedded_chunks = self.embed_chunks(chunks, project_id, document_id, user_id)
            
            # Insert into Supabase
            success = self.insert_into_supabase(embedded_chunks)
            
            if success:
                logger.info(f"Successfully embedded and stored {len(embedded_chunks)} chunks")
                return True
            else:
                logger.error("Failed to insert embedded chunks into Supabase")
                return False
            
        except Exception as e:
            logger.error(f"Error embedding chunks: {str(e)}", exc_info=True)
            return False

def main():
    """Main function to embed chunks into Supabase."""
    # Define paths
    script_dir = os.path.dirname(os.path.abspath(__file__))
    input_file = os.path.join(script_dir, "..", "..", "output", "chunked_research.json")
    
    # Process the chunks
    embedder = PDFEmbedder(input_file)
    # For testing, use a sample project_id and user_id
    success = embedder.process(project_id=1, user_id="test-user-id")
    
    if success:
        logger.info("Successfully embedded and stored chunks")
    else:
        logger.error("Failed to embed and store chunks")

if __name__ == "__main__":
    main() 