import os
import json
from typing import Dict, Any, Optional, List
from pathlib import Path
from app.core.config import logger
from app.services.pdf_parser import PDFParser
from app.services.pdf_chunker import PDFChunker, PAGE_CHUNKING
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
    
    async def ingest_pdf(
            self, 
            pdf_path: str, 
            project_id: Optional[int] = None, 
            user_id: Optional[str] = None,
            custom_document_name: Optional[str] = None,
            original_filename: Optional[str] = None,
            summary: Optional[str] = None
        ) -> Dict[str, Any]:
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
            custom_document_name: Optional custom name to use for the document
            original_filename: Original filename of the uploaded file
            summary: Optional summary of the document content
            
        Returns:
            Dict with status and statistics about the ingestion process
        """
        try:
            # Log project ID information
            logger.info(f"Starting PDF ingestion for {pdf_path} with project_id={project_id} (type: {type(project_id)})")
            logger.info(f"Custom document name: {custom_document_name}, Original filename: {original_filename}")
            if summary:
                logger.info(f"Summary provided: {summary[:100]}...")
            
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
            
            # If custom document name is provided, we'll use it for display but keep the original document_id for file paths
            original_document_id = document_id
            display_name = original_filename or document_id
            
            if custom_document_name:
                # Keep the extension for display
                if not custom_document_name.lower().endswith('.pdf'):
                    display_name = f"{custom_document_name}.pdf"
                else:
                    display_name = custom_document_name
                
                logger.info(f"Using custom display name: {display_name} (original document_id: {document_id})")
            
            # Generate a meaningful title from the content if summary is provided
            ai_title = None
            if summary and not custom_document_name:
                # Extract a title from the summary
                from app.core.ai import generate_response
                title_prompt = f"""
                Based on this summary of a document, generate a concise, descriptive title (max 5-7 words):
                {summary}
                
                Return only the title, with no quotes or additional text.
                """
                ai_title = generate_response(title_prompt, summary).strip()
                logger.info(f"Generated AI title: {ai_title}")
                
                # Use the AI-generated title as the display name
                if ai_title:
                    display_name = ai_title
                    logger.info(f"Using AI-generated title as display name: {display_name}")
            
            parsed_json_path = os.path.join(self.output_dir, f"parsed_{original_document_id}.json")
            
            with open(parsed_json_path, 'w', encoding='utf-8') as f:
                json.dump(parsed_output.dict(), f, indent=2)
            
            logger.info(f"Saved parsed PDF to {parsed_json_path}")
            
            # 2. Chunk the parsed content
            chunker = PDFChunker(parsed_json_path, chunking_strategy=PAGE_CHUNKING)
            chunked_json_path = os.path.join(self.output_dir, f"chunked_{original_document_id}.json")
            chunks = chunker.process(output_file=chunked_json_path)
            
            num_chunks = len(chunks)
            logger.info(f"Created {num_chunks} chunks from PDF")
            
            # 3. Generate embeddings and store in database
            embedder = PDFEmbedder(chunked_json_path)
            success = embedder.process(project_id=project_id, document_id=original_document_id, user_id=user_id)
            
            # 4. Update the project's sources list if project_id is provided
            sources_updated = False
            if project_id:
                # Use the display name for source name and custom ID if provided
                source_id = custom_document_name if custom_document_name else original_document_id
                logger.info(f"Attempting to update project {project_id} sources with file {display_name}, using ID {source_id}")
                
                # IMPORTANT: Always update project sources with the summary and AI-generated title
                # Even if embedding failed, we still want to show the source in the projects list
                sources_updated = await self.update_project_sources(
                    project_id, 
                    display_name, 
                    source_id, 
                    summary,
                    ai_title=ai_title
                )
                logger.info(f"Project sources update result: {sources_updated}")
            else:
                logger.warning(f"No project_id provided (value: {project_id}), skipping sources update")
            
            if not success:
                return {
                    "status": "error",
                    "message": "Failed to embed and store chunks, but source information has been saved",
                    "document_id": source_id if custom_document_name else original_document_id,
                    "project_id": project_id,
                    "chunks_created": num_chunks,
                    "chunks_embedded": 0,
                    "sources_updated": sources_updated,
                    "summary": summary,
                    "ai_title": ai_title
                }
            
            return {
                "status": "success",
                "message": "PDF successfully ingested",
                "document_id": source_id if custom_document_name else original_document_id, 
                "project_id": project_id,
                "chunks_created": num_chunks,
                "chunks_embedded": num_chunks,
                "sources_updated": sources_updated,
                "summary": summary,
                "ai_title": ai_title
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
                "sources_updated": False,
                "summary": None,
                "ai_title": None
            }
    
    async def update_project_sources(
        self, 
        project_id: int, 
        filename: str, 
        document_id: str, 
        summary: str = None,
        ai_title: str = None
    ) -> bool:
        """
        Update the project's sources list with the new source
        
        Args:
            project_id: Project ID to update
            filename: Name of the source file (display name)
            document_id: Document ID of the source
            summary: Optional summary of the source content
            ai_title: Optional AI-generated title
            
        Returns:
            True if successful, False otherwise
        """
        try:
            logger.info(f"Updating sources for project {project_id} with file {filename} and document_id {document_id}")
            
            # First, get the current sources list
            logger.info(f"SQL: SELECT sources FROM projects WHERE project_id = {project_id}")
            response = supabase.table("projects").select("sources").eq("project_id", project_id).execute()
            logger.info(f"Response from select query: {response}")
            
            # Check if the response has the expected structure
            if not hasattr(response, 'data'):
                logger.error(f"Failed to select sources: unexpected response structure")
                logger.error(f"Response: {response}")
                return False
                
            if response.data is None or len(response.data) == 0:
                logger.error(f"Project with ID {project_id} not found")
                return False
            
            # Get current sources or initialize empty array
            current_sources = response.data[0].get("sources", []) or []
            logger.info(f"Current sources for project {project_id}: {current_sources}")
            
            # IMPORTANT: Check if we already have a source with this document_id
            # Filter out any existing sources with the same document_id to avoid duplicates
            filtered_sources = [s for s in current_sources if s.get("document_id") != document_id]
            
            # If we filtered out any sources, log it
            if len(filtered_sources) < len(current_sources):
                logger.info(f"Removed {len(current_sources) - len(filtered_sources)} existing source(s) with document_id {document_id}")
            
            # Create new source object
            # Get current timestamp for upload_date
            from datetime import datetime
            upload_date = datetime.now().isoformat()
            
            # Generate a unique source_id
            source_id = f"source_{document_id}_{int(datetime.now().timestamp())}"
            
            # Use AI-generated title if available, otherwise use filename
            display_title = ai_title or filename
            
            # Create the source object with all required fields
            new_source = {
                "name": filename,  # Original filename for backward compatibility
                "title": display_title,  # AI-generated title or filename
                "display_name": display_title,  # Same as title
                "added_at": upload_date,
                "source_id": source_id,
                "document_id": document_id,
                "summary": summary or "",  # Include the summary if provided
                "ai_generated": ai_title is not None  # Flag if the title was AI-generated
            }
            logger.info(f"Adding new source to project {project_id}: {new_source}")
            
            # Add new source to the filtered list
            filtered_sources.append(new_source)
            
            # Update the project with the new sources list
            logger.info(f"SQL: UPDATE projects SET sources = {filtered_sources} WHERE project_id = {project_id}")
            update_response = supabase.table("projects").update({"sources": filtered_sources}).eq("project_id", project_id).execute()
            logger.info(f"Response from update query: {update_response}")
            
            # Check if the update response has the expected structure
            if not hasattr(update_response, 'data'):
                logger.error(f"Failed to update sources: unexpected response structure")
                logger.error(f"Response: {update_response}")
                return False
                
            if update_response.data is None:
                logger.error(f"Failed to update sources for project {project_id}")
                return False
            
            logger.info(f"Successfully updated sources for project {project_id}. New sources list: {filtered_sources}")
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