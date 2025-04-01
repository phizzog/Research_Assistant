from typing import Optional, List, Dict, Any, Union
from pydantic import BaseModel, Field

# Request/Response models
class QueryRequest(BaseModel):
    query: str
    top_k: Optional[int] = 5
    project_id: Optional[int] = None
    selected_document_ids: Optional[List[str]] = None
    enhanced_queries: Optional[bool] = True

class MessageRequest(BaseModel):
    message: str
    chat_history: Optional[List[Dict[str, str]]] = []
    enhanced_queries: Optional[bool] = True

class ChatWithProjectRequest(BaseModel):
    message: str
    project_id: int
    chat_history: Optional[List[Dict[str, str]]] = []
    enhanced_queries: Optional[bool] = True
    selected_document_ids: Optional[List[str]] = None

class FileUploadRequest(BaseModel):
    file_content: str
    filename: str

class ResponseModel(BaseModel):
    """Model for simple text responses"""
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

# PDF Ingestion Models
class PDFIngestionResponse(BaseModel):
    """
    Model for PDF ingestion response
    
    This is the detailed response format for the /ingest endpoint when simple_mode=False.
    For a simpler response (like the deprecated /upload endpoint), use simple_mode=True.
    """
    status: str = Field(..., description="Success status: 'success' or 'error'")
    message: str = Field(..., description="Message describing the result")
    document_id: Optional[str] = Field(None, description="ID of the processed document")
    project_id: Optional[int] = Field(None, description="Project ID the document was associated with")
    chunks_created: int = Field(0, description="Number of content chunks created")
    chunks_embedded: int = Field(0, description="Number of chunks with embeddings stored")
    sources: Optional[List[Dict[str, Any]]] = Field(None, description="List of sources in the project")
    sources_updated: bool = Field(False, description="Whether the project's sources list was updated")

# Source Models
class Source(BaseModel):
    """Model for source data in database"""
    id: Optional[int] = None
    source_id: str
    chunk_id: str
    raw_text: str
    embedding: Optional[List[float]] = None
    metadata: Optional[Dict[str, Any]] = None
    project_id: Optional[int] = None

class ProjectSource(BaseModel):
    """Model for project source reference"""
    name: str
    document_id: str

# Tavily Source Suggestion Models
class ProjectInfo(BaseModel):
    """Model for project information"""
    title: str
    goals: str

class SourceSuggestionRequest(BaseModel):
    """Request model for suggesting additional sources"""
    project_id: int
    project: ProjectInfo
    sources: List[Dict[str, Any]]

class GapIdentification(BaseModel):
    """Model for a knowledge gap"""
    gap_description: str
    importance: int
    suggested_queries: List[str]

class SearchResult(BaseModel):
    """Model for a search result from Tavily"""
    title: str
    url: str
    content: str
    score: float

class SearchQueryResult(BaseModel):
    """Model for results of a search query"""
    gap_description: str
    query: str
    results: List[SearchResult]

class SourceSuggestionResponse(BaseModel):
    """Response model for suggest-sources endpoint"""
    identified_gaps: List[GapIdentification]
    new_sources_count: int
    new_sources: List[Dict[str, Any]]

# New models for the revised workflow
class GapAnalysisResponse(BaseModel):
    """Response model for identify-gaps endpoint"""
    identified_gaps: List[GapIdentification]

class GapSearchRequest(BaseModel):
    """Request model for search-for-gap endpoint"""
    project_id: int
    gap: GapIdentification

class GapSearchResponse(BaseModel):
    """Response model for search-for-gap endpoint"""
    results: List[SearchResult] 