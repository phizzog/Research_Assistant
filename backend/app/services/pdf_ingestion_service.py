import os
import json
from typing import Dict, Any, Optional, List
from pathlib import Path
from app.core.config import logger
from app.services.pdf_parser import PDFParser
from app.services.pdf_chunker import PDFChunker
from app.services.pdf_embedder import PDFEmbedder
from app.models.schemas import ParserOutput
from app.core.database import supabase

class PDFIngestionService:
    """Service for ingesting PDFs: parsing, chunking, and embedding"""
    
    def __init__(self):
        """Initialize the PDF ingestion service"""
        # Create necessary directories
        self.input_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "input")
        self.output_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "output")
        os.makedirs(self.input_dir, exist_ok=True)
        os.makedirs(self.output_dir, exist_ok=True)
    
    async def ingest_pdf(self, pdf_path: str, project_id: Optional[int] = None, user_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Process a PDF file through the entire ingestion pipeline:
        1. Parse the PDF to extract text and tables
        2. Chunk the parsed content
        3. Generate embeddings and store in the database
        4. Update the project's sources list
        
        Args:
            pdf_path: Path to the PDF file
            project_id: Optional project ID to associate with the chunks
            user_id: Optional user ID to associate with the chunks
            
        Returns:
            Dict with status and statistics about the ingestion process
        """
        try:
            # Log project ID information
            logger.info(f"Starting PDF ingestion for {pdf_path} with project_id={project_id} (type: {type(project_id)})")
            
            # Ensure project_id is an integer if provided
            if project_id is not None:
                try:
                    project_id = int(project_id)
                    logger.info(f"Converted project_id to int: {project_id}")
                except (ValueError, TypeError) as e:
                    logger.error(f"Error converting project_id to int: {e}")
                    project_id = None
            
            # 1. Parse PDF
            parser = PDFParser(pdf_path)
            parsed_output: ParserOutput = await parser.parse_pdf()
            
            # Save parsed output to JSON
            document_id = parsed_output.document.document_id
            parsed_json_path = os.path.join(self.output_dir, f"parsed_{document_id}.json")
            
            with open(parsed_json_path, 'w', encoding='utf-8') as f:
                json.dump(parsed_output.dict(), f, indent=2)
            
            logger.info(f"Saved parsed PDF to {parsed_json_path}")
            
            # 2. Chunk the parsed content
            chunker = PDFChunker(parsed_json_path)
            chunked_json_path = os.path.join(self.output_dir, f"chunked_{document_id}.json")
            chunks = chunker.process(output_file=chunked_json_path)
            
            logger.info(f"Created {len(chunks)} chunks from PDF")
            
            # 3. Generate embeddings and store in database
            embedder = PDFEmbedder(chunked_json_path)
            success = embedder.process(project_id=project_id, document_id=document_id, user_id=user_id)
            
            # 4. Update the project's sources list if project_id is provided
            sources_updated = False
            if project_id and success:
                filename = os.path.basename(pdf_path)
                logger.info(f"Attempting to update project {project_id} sources with file {filename}")
                sources_updated = await self.update_project_sources(project_id, filename, document_id)
                logger.info(f"Project sources update result: {sources_updated}")
            else:
                if not project_id:
                    logger.warning(f"No project_id provided (value: {project_id}), skipping sources update")
                if not success:
                    logger.warning("Embedding process failed, skipping sources update")
            
            if not success:
                return {
                    "status": "error",
                    "message": "Failed to embed and store chunks",
                    "document_id": document_id,
                    "project_id": project_id,
                    "chunks_created": len(chunks),
                    "chunks_embedded": 0,
                    "sources_updated": sources_updated
                }
            
            return {
                "status": "success",
                "message": "PDF successfully ingested",
                "document_id": document_id,
                "project_id": project_id,
                "chunks_created": len(chunks),
                "chunks_embedded": len(chunks),
                "sources_updated": sources_updated
            }
            
        except Exception as e:
            logger.error(f"Error ingesting PDF: {str(e)}", exc_info=True)
            return {
                "status": "error",
                "message": f"Error ingesting PDF: {str(e)}",
                "document_id": None,
                "project_id": project_id,
                "chunks_created": 0,
                "chunks_embedded": 0,
                "sources_updated": False
            }
    
    async def update_project_sources(self, project_id: int, filename: str, document_id: str) -> bool:
        """
        Update the project's sources list with the new source
        
        Args:
            project_id: Project ID to update
            filename: Name of the source file
            document_id: Document ID of the source
            
        Returns:
            True if successful, False otherwise
        """
        try:
            logger.info(f"Updating sources for project {project_id} with file {filename}")
            
            # First, get the current sources list
            logger.info(f"SQL: SELECT sources FROM projects WHERE project_id = {project_id}")
            response = supabase.table("projects").select("sources").eq("project_id", project_id).execute()
            logger.info(f"Response from select query: {response}")
            
            if not response.data or len(response.data) == 0:
                logger.error(f"Project with ID {project_id} not found")
                return False
            
            # Get current sources or initialize empty array
            current_sources = response.data[0].get("sources", []) or []
            logger.info(f"Current sources for project {project_id}: {current_sources}")
            
            # Create new source object
            new_source = {
                "name": filename,
                "document_id": document_id,
                "upload_date": supabase.table("projects").select("created_at").execute().data[0]["created_at"]
            }
            logger.info(f"Adding new source to project {project_id}: {new_source}")
            
            # Add new source to the list
            current_sources.append(new_source)
            
            # Update the project with the new sources list
            logger.info(f"SQL: UPDATE projects SET sources = {current_sources} WHERE project_id = {project_id}")
            update_response = supabase.table("projects").update({"sources": current_sources}).eq("project_id", project_id).execute()
            logger.info(f"Response from update query: {update_response}")
            
            if not update_response.data:
                logger.error(f"Failed to update sources for project {project_id}: {update_response.error}")
                return False
            
            logger.info(f"Successfully updated sources for project {project_id}. New sources list: {current_sources}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating project sources: {str(e)}", exc_info=True)
            return False
    
    async def batch_ingest_pdfs(self, pdf_paths: List[str], project_id: Optional[int] = None, user_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Process multiple PDF files through the ingestion pipeline
        
        Args:
            pdf_paths: List of paths to PDF files
            project_id: Optional project ID to associate with the chunks
            user_id: Optional user ID to associate with the chunks
            
        Returns:
            List of dictionaries with status and statistics for each PDF
        """
        results = []
        for pdf_path in pdf_paths:
            result = await self.ingest_pdf(pdf_path, project_id, user_id)
            results.append(result)
        
        return results 