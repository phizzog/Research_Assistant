import json
import os
import logging
import time
from typing import List, Dict, Any
from app.core.database import supabase
from app.core.ai import generate_embeddings
from app.core.config import logger

class PDFEmbedder:
    """Class for embedding PDF chunks into vector database"""
    
    def __init__(self, input_file: str = None):
        """Initialize the PDF embedder with input file path"""
        self.input_file = input_file
    
    def load_json(self, file_path: str = None) -> Dict[str, Any]:
        """Load JSON data from a file."""
        file_path = file_path or self.input_file
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
            
            # Add project_id if provided
            if project_id:
                record["metadata"]["project_id"] = project_id
                
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
                # Use upsert with chunk_id as the conflict resolution key
                response = supabase.table(table_name).upsert(batch, on_conflict="chunk_id").execute()
                
                if not response.data:
                    logger.error(f"Failed to insert batch {i//batch_size + 1}: {response.error}")
                    return False
                
                logger.info(f"Inserted batch {i//batch_size + 1}/{(len(embedded_chunks)-1)//batch_size + 1}")
            
            logger.info(f"Successfully inserted all {len(embedded_chunks)} chunks")
            return True
            
        except Exception as e:
            logger.error(f"Error inserting chunks into Supabase: {str(e)}")
            return False
    
    def process(self, input_file: str = None, project_id: int = None, document_id: str = None, user_id: str = None, table_name: str = "sources") -> bool:
        """Process chunks, generate embeddings, and store in Supabase"""
        try:
            # Set input file if provided
            if input_file:
                self.input_file = input_file
                
            # Ensure input file is set
            if not self.input_file:
                raise ValueError("Input file path is required")
                
            # Load JSON
            data = self.load_json()
            chunks = data.get("chunks", [])
            
            if not chunks:
                logger.warning("No chunks found in input file")
                return False
                
            logger.info(f"Processing {len(chunks)} chunks from document_id: {document_id}")
                
            # Generate embeddings
            embedded_chunks = self.embed_chunks(chunks, project_id, document_id, user_id)
            
            logger.info(f"Generated embeddings for {len(embedded_chunks)} chunks")
            
            # Insert into Supabase using the sources table
            success = self.insert_into_supabase(embedded_chunks, table_name)
            
            if success:
                logger.info(f"Successfully processed and stored {len(embedded_chunks)} chunks")
            else:
                logger.error(f"Failed to store {len(embedded_chunks)} chunks")
                
            return success
            
        except Exception as e:
            logger.error(f"Error processing chunks: {str(e)}", exc_info=True)
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