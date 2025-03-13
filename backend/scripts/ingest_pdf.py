#!/usr/bin/env python
"""
PDF Ingestion Script

This script allows you to ingest a PDF file through the complete pipeline:
1. Parse the PDF to extract text and tables
2. Chunk the parsed content
3. Generate embeddings and store in the database

Usage:
    python ingest_pdf.py --pdf_path /path/to/your/file.pdf [--project_id 123]

Arguments:
    --pdf_path: Path to the PDF file to ingest
    --project_id: (Optional) Project ID to associate with the chunks
    --user_id: (Optional) User ID to associate with the chunks
"""

import os
import sys
import argparse
import asyncio
from pathlib import Path

# Add the parent directory to the Python path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.services.pdf_ingestion_service import PDFIngestionService
from app.core.config import logger

async def main():
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="Ingest a PDF file into the Research Assistant")
    parser.add_argument("--pdf_path", required=True, help="Path to the PDF file to ingest")
    parser.add_argument("--project_id", type=int, help="Project ID to associate with the chunks")
    parser.add_argument("--user_id", help="User ID to associate with the chunks")
    args = parser.parse_args()
    
    # Validate PDF path
    pdf_path = args.pdf_path
    if not os.path.exists(pdf_path):
        logger.error(f"PDF file not found: {pdf_path}")
        sys.exit(1)
    
    if not pdf_path.lower().endswith('.pdf'):
        logger.error(f"File is not a PDF: {pdf_path}")
        sys.exit(1)
    
    # Initialize the ingestion service
    ingestion_service = PDFIngestionService()
    
    # Process the PDF
    logger.info(f"Starting ingestion of PDF: {pdf_path}")
    result = await ingestion_service.ingest_pdf(pdf_path, args.project_id, args.user_id)
    
    # Print the result
    if result["status"] == "success":
        logger.info(f"Successfully ingested PDF: {pdf_path}")
        logger.info(f"Document ID: {result['document_id']}")
        logger.info(f"Chunks created: {result['chunks_created']}")
        logger.info(f"Chunks embedded: {result['chunks_embedded']}")
    else:
        logger.error(f"Failed to ingest PDF: {result['message']}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main()) 