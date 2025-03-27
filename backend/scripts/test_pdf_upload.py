#!/usr/bin/env python
"""
Test script to upload a PDF file with project_id and verify it's properly stored.
This helps diagnose issues with project_id being NULL in the sources table.
"""

import os
import sys
import asyncio
import argparse
from dotenv import load_dotenv

# Add the parent directory to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import required modules
from app.services.pdf_ingestion_service import PDFIngestionService
from app.core.config import logger

async def test_pdf_upload(pdf_path: str, project_id: int):
    """Test uploading a PDF with project_id"""
    
    logger.info(f"Testing PDF upload with path={pdf_path}, project_id={project_id}")
    
    # Initialize the ingestion service
    ingestion_service = PDFIngestionService()
    
    # Ingest the PDF
    result = await ingestion_service.ingest_pdf(pdf_path, project_id)
    
    logger.info(f"Ingestion result: {result}")
    
    # Verify the result
    if result["status"] == "success":
        logger.info("✅ PDF ingestion successful")
        logger.info(f"Document ID: {result['document_id']}")
        logger.info(f"Project ID: {result['project_id']}")
        logger.info(f"Chunks created: {result['chunks_created']}")
        logger.info(f"Chunks embedded: {result['chunks_embedded']}")
        logger.info(f"Sources updated: {result['sources_updated']}")
        
        # Now verify the source has the correct project_id
        from app.core.database import supabase
        from scripts.verify_sources_project_id import verify_sources_project_id
        
        # Get chunks for this document
        document_id = result["document_id"]
        logger.info(f"Verifying sources for document_id containing {document_id}")
        
        # Query using LIKE since the source_id might have a timestamp or other suffix
        sources_response = supabase.table("sources").select("id, source_id, chunk_id, project_id").like("source_id", f"source_{document_id}%").execute()
        
        sources = sources_response.data
        logger.info(f"Found {len(sources)} sources for document_id {document_id}")
        
        if sources:
            correct_project_id = sum(1 for s in sources if s.get("project_id") == project_id)
            logger.info(f"Sources with correct project_id={project_id}: {correct_project_id}/{len(sources)}")
            
            if correct_project_id == len(sources):
                logger.info("✅ All sources have the correct project_id")
            else:
                logger.warning("❌ Some sources do not have the correct project_id")
                
                # Display the first 5 sources with incorrect project_id
                incorrect_sources = [s for s in sources if s.get("project_id") != project_id][:5]
                for i, source in enumerate(incorrect_sources):
                    logger.warning(f"  {i+1}. id: {source.get('id')}, project_id: {source.get('project_id')}")
        
        # Run a general verification as well
        logger.info("\nGeneral verification of all sources:")
        verify_sources_project_id()
        
        return result
    else:
        logger.error(f"❌ PDF ingestion failed: {result['message']}")
        return result

if __name__ == "__main__":
    # Load environment variables
    load_dotenv()
    
    parser = argparse.ArgumentParser(description="Test PDF upload with project_id")
    parser.add_argument("pdf_path", help="Path to the PDF file to upload")
    parser.add_argument("project_id", type=int, help="Project ID to associate with the PDF")
    args = parser.parse_args()
    
    # Check if the PDF file exists
    if not os.path.isfile(args.pdf_path):
        logger.error(f"PDF file not found: {args.pdf_path}")
        sys.exit(1)
    
    # Run the test
    asyncio.run(test_pdf_upload(args.pdf_path, args.project_id)) 