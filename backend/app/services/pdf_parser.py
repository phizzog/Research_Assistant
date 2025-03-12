import os
import pdfplumber
import pytesseract
from PIL import Image
import pandas as pd
from pdf2image import convert_from_path
from pathlib import Path
from io import BytesIO
import base64
from typing import List, Any
from app.models.schemas import Table, PDFPage, PDFDocument, ParserOutput
from app.core.config import logger

def pil_image_to_base64(img: Image.Image) -> str:
    """
    Convert a PIL Image to a base64-encoded JPEG string.
    """
    buffered = BytesIO()
    img.save(buffered, format="JPEG")
    img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")
    return img_str

class PDFParser:
    """Main PDF parser class that coordinates text and table extraction"""
    
    def __init__(self, pdf_path: str):
        """Initialize the PDF parser with the path to the PDF file"""
        self.pdf_path = pdf_path
        # Debug: Track the current page being processed
        self.current_page = 0
    
    async def parse_pdf(self) -> ParserOutput:
        """Parse the entire PDF document"""
        try:
            # Debug: Opening PDF file
            logger.info(f"Opening PDF file: {self.pdf_path}")
            with pdfplumber.open(self.pdf_path) as pdf:
                # Create document metadata
                document = PDFDocument(
                    document_id=self.pdf_path.split("/")[-1],
                    filename=self.pdf_path.split("/")[-1],
                    total_pages=len(pdf.pages),
                    metadata=pdf.metadata or {}
                )
                
                # Parse each page
                pages = []
                for i, page in enumerate(pdf.pages):
                    self.current_page = i + 1
                    logger.info(f"Processing page {self.current_page}/{document.total_pages}")
                    
                    # Extract text and tables
                    text = self._extract_text(page)
                    tables = self._extract_tables(page)
                    
                    # Create page model
                    pdf_page = PDFPage(
                        page_id=f"page_{i+1}",
                        pdf_title=document.filename,
                        text=text,
                        tables=tables
                    )
                    pages.append(pdf_page)
                
                return ParserOutput(document=document, pages=pages)
                
        except Exception as e:
            logger.error(f"Error parsing PDF: {str(e)}")
            raise
    
    def _extract_text(self, page: Any) -> str:
        """Extract text from a PDF page"""
        try:
            # Debug: Extracting text from page
            logger.debug(f"Extracting text from page {self.current_page}")
            text = page.extract_text() or ""
            return text.strip()
        except Exception as e:
            logger.error(f"Error extracting text from page {self.current_page}: {str(e)}")
            return ""
    
    def _extract_tables(self, page: Any) -> List[Table]:
        """Extract tables from a PDF page"""
        try:
            # Debug: Extracting tables from page
            logger.debug(f"Extracting tables from page {self.current_page}")
            tables = []
            raw_tables = page.extract_tables()
            
            for i, raw_table in enumerate(raw_tables):
                # Convert table to pandas DataFrame for cleaning
                df = pd.DataFrame(raw_table)
                
                # Clean the table data
                cleaned_data = [
                    [str(cell).strip() if cell is not None else "" for cell in row]
                    for row in df.values.tolist()
                ]
                
                # Create table model
                table = Table(
                    table_id=f"table_{self.current_page}_{i+1}",
                    data=cleaned_data
                )
                tables.append(table)
            
            return tables
        except Exception as e:
            logger.error(f"Error extracting tables from page {self.current_page}: {str(e)}")
            return [] 