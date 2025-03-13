#!/usr/bin/env python
"""
Batch PDF Ingestion Script

This script allows you to ingest multiple PDF files through the complete pipeline:
1. Parse the PDFs to extract text and tables
2. Chunk the parsed content
3. Generate embeddings and store in the database

Usage:
    python batch_ingest_pdfs.py --pdf_dir /path/to/pdf/directory [--project_id 123]

Arguments:
    --pdf_dir: Directory containing PDF files to ingest
    --project_id: (Optional) Project ID to associate with the chunks
"""

import os
import sys
import argparse
import asyncio
from pathlib import Path
from typing import List

# Add the parent directory to the Python path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.services.pdf_ingestion_service import PDFIngestionService
from app.core.config import logger

def find_pdf_files(directory: str) -> List[str]:
    """Find all PDF files in the specified directory"""
    pdf_files = []
    for root, _, files in os.walk(directory):
        for file in files:
            if file.lower().endswith('.pdf'):
                pdf_files.append(os.path.join(root, file))
    return pdf_files

async def main():
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="Batch ingest PDF files into the Research Assistant")
    parser.add_argument("--pdf_dir", required=True, help="Directory containing PDF files to ingest")
    parser.add_argument("--project_id", type=int, help="Project ID to associate with the chunks")
    parser.add_argument("--user_id", help="User ID to associate with the chunks")
    args = parser.parse_args()
    
    # Validate PDF directory
    pdf_dir = args.pdf_dir
    if not os.path.exists(pdf_dir) or not os.path.isdir(pdf_dir):
        logger.error(f"PDF directory not found: {pdf_dir}")
        sys.exit(1)
    
    # Find PDF files
    pdf_files = find_pdf_files(pdf_dir)
    if not pdf_files:
        logger.error(f"No PDF files found in directory: {pdf_dir}")
        sys.exit(1)
    
    logger.info(f"Found {len(pdf_files)} PDF files to process")
    
    # Initialize the ingestion service
    ingestion_service = PDFIngestionService()
    
    # Process the PDFs
    results = await ingestion_service.batch_ingest_pdfs(pdf_files, args.project_id, args.user_id)
    
    # Print the results
    success_count = sum(1 for result in results if result["status"] == "success")
    error_count = len(results) - success_count
    
    logger.info(f"Batch ingestion complete: {success_count} succeeded, {error_count} failed")
    
    # Print details for each PDF
    for i, result in enumerate(results):
        pdf_path = pdf_files[i]
        if result["status"] == "success":
            logger.info(f"✅ {os.path.basename(pdf_path)}: {result['chunks_created']} chunks created, {result['chunks_embedded']} embedded")
        else:
            logger.error(f"❌ {os.path.basename(pdf_path)}: {result['message']}")
    
    if error_count > 0:
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main()) 