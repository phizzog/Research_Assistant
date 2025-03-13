import os
import tempfile
from fastapi import APIRouter, UploadFile, File, HTTPException, Form, Query
from app.models.schemas import QueryRequest, MessageRequest, ResponseModel, PDFIngestionResponse
from app.services.pdf_parser import PDFParser
from app.services.document_service import store_pdf_content, get_context_from_query
from app.services.pdf_ingestion_service import PDFIngestionService
from app.core.ai import generate_response
from app.core.config import logger
from typing import Optional, List

router = APIRouter()

@router.post("/query", response_model=ResponseModel)
async def handle_query(request: QueryRequest):
    """Handle query requests"""
    query = request.query
    top_k = request.top_k
    
    if not query:
        return {"answer": "Query is required"}
    
    context = get_context_from_query(query, top_k)
    if not context:
        return {"answer": "No relevant context found. Please try a different query related to research design."}
    
    answer = generate_response(query, context)
    return {"answer": answer}

@router.post("/chat", response_model=ResponseModel)
async def handle_chat(request: MessageRequest):
    """Handle chat messages"""
    message = request.message
    chat_history = request.chat_history
    
    if not message:
        return {"answer": "Message is required"}
    
    context = get_context_from_query(message)
    if not context:
        # If no context found, still try to answer based on general knowledge
        context = "No specific context found in the research design book."
    
    answer = generate_response(message, context, chat_history)
    return {"answer": answer}

@router.post("/upload", response_model=ResponseModel)
async def handle_file_upload(file: UploadFile = File(...)):
    """Handle file uploads"""
    try:
        # Check if the file is a PDF
        if not file.filename.lower().endswith('.pdf'):
            raise HTTPException(status_code=400, detail="Only PDF files are supported")
        
        # Create a temporary file to store the uploaded PDF
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
            # Write the uploaded file content to the temporary file
            content = await file.read()
            temp_file.write(content)
            temp_file_path = temp_file.name
        
        try:
            # Parse the PDF
            parser = PDFParser(temp_file_path)
            pdf_data = await parser.parse_pdf()
            
            # Store the parsed content in Supabase
            chunks_stored = await store_pdf_content(pdf_data)
            
            # Generate a summary of the PDF using Gemini
            # Extract a sample of text for the summary (first page or two)
            sample_text = ""
            for page in pdf_data.pages[:2]:  # First two pages
                sample_text += page.text + "\n\n"
            
            prompt = f"""
            Analyze the following content from a PDF about research design and provide a brief summary:
            
            {sample_text[:4000]}  # Limiting content length for API constraints
            """
            
            response = generate_response(prompt, sample_text)
            
            return {
                "answer": f"Successfully processed PDF '{file.filename}'. {chunks_stored} chunks of content were extracted and stored for future queries. \n\nSummary: {response}"
            }
        finally:
            # Clean up the temporary file
            os.unlink(temp_file_path)
            
    except Exception as e:
        logger.error(f"Error processing PDF file: {e}")
        return {"answer": f"Error processing PDF file: {str(e)}"}

@router.post("/ingest", response_model=PDFIngestionResponse)
async def ingest_pdf(
    file: UploadFile = File(...),
    project_id: Optional[int] = Form(None),
    user_id: Optional[str] = Form(None),
    process_type: str = Form("full")  # Options: "full", "parse_only", "chunk_only", "embed_only"
):
    """
    Ingest a PDF file through the complete pipeline or specific stages
    
    Args:
        file: The PDF file to ingest
        project_id: Optional project ID to associate with the chunks
        user_id: Optional user ID to associate with the chunks
        process_type: Type of processing to perform
            - "full": Complete pipeline (parse, chunk, embed)
            - "parse_only": Only parse the PDF
            - "chunk_only": Only chunk an already parsed PDF
            - "embed_only": Only embed already chunked content
    
    Returns:
        Status and statistics about the ingestion process
    """
    try:
        # Check if the file is a PDF
        if not file.filename.lower().endswith('.pdf'):
            raise HTTPException(status_code=400, detail="Only PDF files are supported")
        
        logger.info(f"Starting ingestion of file {file.filename} for project_id={project_id} (type: {type(project_id)}), user_id={user_id}")
        
        # Validate project_id
        if project_id is not None:
            try:
                project_id = int(project_id)
                logger.info(f"Converted project_id to int: {project_id}")
            except (ValueError, TypeError) as e:
                logger.error(f"Error converting project_id to int: {e}")
                raise HTTPException(status_code=400, detail=f"Invalid project_id: {project_id}. Must be an integer.")
        
        # Create a temporary file to store the uploaded PDF
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
            # Write the uploaded file content to the temporary file
            temp_file.write(await file.read())
            temp_file_path = temp_file.name
        
        try:
            # Initialize the ingestion service
            ingestion_service = PDFIngestionService()
            
            # Process the PDF based on the requested process type
            if process_type == "full":
                logger.info(f"Processing file {file.filename} with process_type={process_type}")
                result = await ingestion_service.ingest_pdf(temp_file_path, project_id, user_id)
                logger.info(f"Ingestion result: {result}")
                
                # If successful and project_id is provided, return the updated project sources
                if result["status"] == "success" and project_id:
                    from app.core.database import supabase
                    # Get the updated project sources
                    logger.info(f"Fetching updated sources for project {project_id}")
                    project_response = supabase.table("projects").select("sources").eq("project_id", project_id).execute()
                    logger.info(f"Project response: {project_response}")
                    
                    if project_response.data and len(project_response.data) > 0:
                        sources = project_response.data[0].get("sources", [])
                        logger.info(f"Retrieved sources for project {project_id}: {sources}")
                        result["sources"] = sources
                    else:
                        logger.warning(f"No sources found for project {project_id} after update. Response data: {project_response.data}")
            else:
                # For future implementation of partial processing
                raise HTTPException(status_code=400, detail=f"Process type '{process_type}' not yet implemented")
            
            return result
        finally:
            # Clean up the temporary file
            os.unlink(temp_file_path)
            
    except Exception as e:
        logger.error(f"Error ingesting PDF: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error ingesting PDF: {str(e)}")

@router.post("/batch-ingest", response_model=List[PDFIngestionResponse])
async def batch_ingest_pdfs(
    files: List[UploadFile] = File(...),
    project_id: Optional[int] = Form(None),
    user_id: Optional[str] = Form(None)
):
    """
    Batch ingest multiple PDF files
    
    Args:
        files: List of PDF files to ingest
        project_id: Optional project ID to associate with the chunks
        user_id: Optional user ID to associate with the chunks
    
    Returns:
        List of status and statistics about each ingestion process
    """
    try:
        # Check if all files are PDFs
        for file in files:
            if not file.filename.lower().endswith('.pdf'):
                raise HTTPException(status_code=400, detail=f"Only PDF files are supported. '{file.filename}' is not a PDF.")
        
        # Create temporary files for all uploaded PDFs
        temp_file_paths = []
        for file in files:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
                temp_file.write(await file.read())
                temp_file_paths.append(temp_file.name)
        
        try:
            # Initialize the ingestion service
            ingestion_service = PDFIngestionService()
            
            # Process all PDFs
            results = await ingestion_service.batch_ingest_pdfs(temp_file_paths, project_id, user_id)
            
            return results
        finally:
            # Clean up all temporary files
            for temp_file_path in temp_file_paths:
                os.unlink(temp_file_path)
                
    except Exception as e:
        logger.error(f"Error batch ingesting PDFs: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error batch ingesting PDFs: {str(e)}")

@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "ok"} 