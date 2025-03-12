import os
import tempfile
from fastapi import APIRouter, UploadFile, File, HTTPException
from app.models.schemas import QueryRequest, MessageRequest, ResponseModel
from app.services.pdf_parser import PDFParser
from app.services.document_service import store_pdf_content, get_context_from_query
from app.core.ai import generate_response
from app.core.config import logger

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

@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"} 