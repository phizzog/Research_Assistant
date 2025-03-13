#!/usr/bin/env python
"""
Test PDF Ingestion Script

This script tests the PDF ingestion pipeline by:
1. Creating a simple test PDF
2. Running the ingestion process
3. Verifying the results

Usage:
    python test_ingestion.py
"""

import os
import sys
import asyncio
import tempfile
from pathlib import Path
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter

# Add the parent directory to the Python path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.services.pdf_ingestion_service import PDFIngestionService
from app.core.config import logger

def create_test_pdf(output_path: str):
    """Create a simple test PDF with some text"""
    c = canvas.Canvas(output_path, pagesize=letter)
    
    # Add a title
    c.setFont("Helvetica-Bold", 16)
    c.drawString(100, 750, "Test Research Paper")
    
    # Add some sections and paragraphs
    c.setFont("Helvetica-Bold", 12)
    c.drawString(100, 700, "INTRODUCTION")
    
    c.setFont("Helvetica", 10)
    c.drawString(100, 680, "This is a test PDF for the Research Assistant ingestion pipeline.")
    c.drawString(100, 670, "It contains multiple sections and paragraphs to test the chunking process.")
    
    c.setFont("Helvetica-Bold", 12)
    c.drawString(100, 630, "METHODOLOGY")
    
    c.setFont("Helvetica", 10)
    c.drawString(100, 610, "The methodology section describes the approach used in this research.")
    c.drawString(100, 600, "We used a mixed-methods approach combining qualitative and quantitative data.")
    
    c.setFont("Helvetica-Bold", 12)
    c.drawString(100, 560, "RESULTS")
    
    c.setFont("Helvetica", 10)
    c.drawString(100, 540, "The results of our analysis show significant findings in several areas.")
    c.drawString(100, 530, "Statistical analysis revealed p < 0.05 for all primary hypotheses.")
    
    c.setFont("Helvetica-Bold", 12)
    c.drawString(100, 490, "CONCLUSION")
    
    c.setFont("Helvetica", 10)
    c.drawString(100, 470, "In conclusion, our research demonstrates the effectiveness of the approach.")
    c.drawString(100, 460, "Future work should explore additional dimensions of this problem space.")
    
    # Add a second page
    c.showPage()
    
    c.setFont("Helvetica-Bold", 12)
    c.drawString(100, 750, "REFERENCES")
    
    c.setFont("Helvetica", 10)
    c.drawString(100, 730, "1. Smith, J. (2023). Research methods in the digital age.")
    c.drawString(100, 720, "2. Johnson, A. & Williams, B. (2022). Data analysis techniques.")
    c.drawString(100, 710, "3. Brown, C. et al. (2021). Machine learning applications in research.")
    
    c.save()
    logger.info(f"Created test PDF at {output_path}")

async def main():
    """Main function to test the PDF ingestion pipeline"""
    # Create a temporary directory for the test
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create a test PDF
        test_pdf_path = os.path.join(temp_dir, "test_research.pdf")
        create_test_pdf(test_pdf_path)
        
        # Initialize the ingestion service
        ingestion_service = PDFIngestionService()
        
        # Process the PDF
        logger.info(f"Starting ingestion of test PDF: {test_pdf_path}")
        # Use a test project_id and user_id
        test_project_id = 999
        test_user_id = "test-user-123"
        result = await ingestion_service.ingest_pdf(test_pdf_path, project_id=test_project_id, user_id=test_user_id)
        
        # Print the result
        if result["status"] == "success":
            logger.info("✅ Test successful!")
            logger.info(f"Document ID: {result['document_id']}")
            logger.info(f"Chunks created: {result['chunks_created']}")
            logger.info(f"Chunks embedded: {result['chunks_embedded']}")
        else:
            logger.error(f"❌ Test failed: {result['message']}")
            sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main()) 