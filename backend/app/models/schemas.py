from typing import Optional, List, Dict, Any
from pydantic import BaseModel

# Request/Response models
class QueryRequest(BaseModel):
    query: str
    top_k: Optional[int] = 5

class MessageRequest(BaseModel):
    message: str
    chat_history: Optional[List[Dict[str, str]]] = []

class FileUploadRequest(BaseModel):
    file_content: str
    filename: str

class ResponseModel(BaseModel):
    answer: str

# PDF Parser Models
class Table(BaseModel):
    """Model for table data extracted from PDF"""
    table_id: str
    data: List[List[str]]

class PDFPage(BaseModel):
    """Model for parsed page content"""
    page_id: str
    pdf_title: str
    text: str
    tables: List[Table]

class PDFDocument(BaseModel):
    """Model for PDF document metadata"""
    document_id: str
    filename: str
    total_pages: int
    metadata: Dict[str, Any]

class ParserOutput(BaseModel):
    """Model for complete parser output"""
    document: PDFDocument
    pages: List[PDFPage] 