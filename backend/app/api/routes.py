import os
import tempfile
from fastapi import APIRouter, UploadFile, File, HTTPException, Form, Query, Depends
from fastapi.responses import JSONResponse
from typing import Optional, List, Union
from app.models.schemas import QueryRequest, MessageRequest, ResponseModel, PDFIngestionResponse, ChatWithProjectRequest
from app.services.pdf_parser import PDFParser
from app.services.document_service import (
    store_pdf_content, 
    get_context_from_query, 
    get_context_for_project,
    get_context_for_project_with_selected_documents
)
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
    project_id = request.project_id
    selected_document_ids = request.selected_document_ids
    enhanced_queries = request.enhanced_queries if hasattr(request, 'enhanced_queries') else True
    
    if not query:
        return {"answer": "Query is required"}
    
    # Check if it's a greeting or help request
    greeting_phrases = ["hi", "hello", "hey", "greetings", "hi there", "help", "help me", "i need help"]
    is_greeting = query.lower().strip() in greeting_phrases or query.lower().startswith("help with") or query.lower().startswith("how do i")
    
    if is_greeting:
        # Handle greetings and help requests directly without context
        greeting_response = generate_greeting_response(query)
        return {"answer": greeting_response}
    
    # Start with an empty combined context
    combined_context = ""
    context_sources = []
    
    # Get project details if project_id is provided
    project_info = ""
    if project_id is not None:
        try:
            # Fetch project details from database
            from app.core.database import supabase
            # Fetch more project metadata including research_type and learning_objective
            project_response = supabase.table("projects").select("project_name, description, research_type, learning_objective").eq("project_id", project_id).execute()
            
            if project_response.data and len(project_response.data) > 0:
                project_name = project_response.data[0].get("project_name", "")
                project_description = project_response.data[0].get("description", "")
                research_type = project_response.data[0].get("research_type", "")
                learning_objective = project_response.data[0].get("learning_objective", "")
                
                # Include current user query purpose
                current_goal = f"Current Question: {query}"
                
                # Build comprehensive project info
                project_info = f"Project Name: {project_name}\n"
                if project_description:
                    project_info += f"Project Description: {project_description}\n"
                if research_type:
                    project_info += f"Research Type: {research_type}\n"
                if learning_objective:
                    project_info += f"Learning Objective: {learning_objective}\n"
                project_info += f"{current_goal}"
                    
                logger.info(f"Retrieved enhanced project info: {project_info}")
                
                # Check if selected documents exist in the database
                if selected_document_ids:
                    # Use a direct SQL query to get distinct document IDs for this project
                    doc_query = f"""
                    SELECT DISTINCT metadata->>'document_id' as doc_id, metadata->>'source' as source 
                    FROM sources 
                    WHERE project_id = {project_id} AND metadata IS NOT NULL
                    """
                    doc_response = supabase.table("sources").select("metadata->document_id, metadata->source").eq("project_id", project_id).execute()
                    
                    # Extract unique document IDs from the response
                    available_doc_ids = set()
                    available_sources = set()
                    
                    for item in doc_response.data:
                        metadata = item.get("metadata", {})
                        if metadata and isinstance(metadata, dict):
                            doc_id = metadata.get("document_id")
                            source = metadata.get("source")
                            if doc_id:
                                available_doc_ids.add(doc_id)
                            if source:
                                available_sources.add(source)
                    
                    logger.info(f"Available document IDs in project {project_id}: {available_doc_ids}")
                    logger.info(f"Available sources in project {project_id}: {available_sources}")
                    
                    # Check if selected documents exist in the available ones
                    found_docs = []
                    for selected_id in selected_document_ids:
                        if selected_id in available_doc_ids or selected_id in available_sources:
                            found_docs.append(selected_id)
                            continue
                        
                        # Try partial matches
                        found = False
                        for avail_id in available_doc_ids:
                            if selected_id in avail_id or avail_id in selected_id:
                                found_docs.append(selected_id)
                                found = True
                                break
                        
                        if not found:
                            for avail_source in available_sources:
                                if selected_id in avail_source or avail_source in selected_id:
                                    found_docs.append(selected_id)
                                    break
                    
                    logger.info(f"Found {len(found_docs)}/{len(selected_document_ids)} selected documents in the database")
        except Exception as e:
            logger.error(f"Error fetching project details: {e}", exc_info=True)
    
    # Always check project-specific sources first if project_id is provided
    if project_id is not None:
        from app.core.database import supabase
        from app.services.document_service import (
            get_context_for_project_intermediate, 
            get_context_for_project_with_selected_documents_intermediate
        )
        
        # If selected document IDs are provided, use the filtering function
        if selected_document_ids:
            logger.info(f"Fetching context from selected documents: {selected_document_ids}")
            # Use the intermediate function that accepts supabase client
            project_context = get_context_for_project_with_selected_documents_intermediate(
                supabase,
                project_id, 
                selected_document_ids, 
                query,
                project_info
            )
            logger.info(f"Retrieved context from project with selected documents")
            # Since the function doesn't return a tuple yet, we'll set num_chunks manually for now
            num_chunks = 1 if project_context else 0
        else:
            # Otherwise, use all documents in the project
            logger.info(f"Fetching context from all project documents")
            # Use the intermediate function that accepts supabase client
            project_context = get_context_for_project_intermediate(
                supabase,
                project_id, 
                query,
                project_info
            )
            logger.info(f"Retrieved context from project")
            # Since the function doesn't return a tuple yet, we'll set num_chunks manually for now
            num_chunks = 1 if project_context else 0
            
        if project_context:
            combined_context += project_context
            context_sources.append(f"project ({num_chunks} chunks)")
    
    # Always query the book's chunks database as well
    try:
        from app.services.book_service import get_context_from_book
        # Pass project info to book search as well for more context
        book_context, book_chunks = get_context_from_book(
            query, 
            5,
            use_enhanced_queries=enhanced_queries,
            project_info=project_info
        )
        if book_context:
            # Add separator if we already have project context
            if combined_context:
                combined_context += "\n\n--- From Research Framework Book ---\n\n"
            combined_context += book_context
            context_sources.append(f"book ({book_chunks} chunks)")
    except ImportError:
        # If book_service doesn't exist yet, use the fallback
        logger.warning("book_service module not found, using fallback")
        if not combined_context:
            # Only get context from general query if we don't have project context
            book_context = get_context_from_query(
                query, 
                top_k,
                use_enhanced_queries=enhanced_queries
            )
            if book_context:
                combined_context += book_context
                context_sources.append("general")
    
    # Log the sources used for context
    logger.info(f"Retrieved context from sources: {', '.join(context_sources)}")
    
    # If we still don't have any context, respond accordingly
    if not combined_context:
        return {"answer": "I don't have enough context to answer that question. Please try a different query or upload relevant sources to your project."}
    
    # Debug log to help troubleshoot context issues
    logger.info(f"Combined context length: {len(combined_context)} characters")
    logger.info(f"First 300 characters of context: {combined_context[:300]}...")
    
    # Generate the response with the combined context and project info
    answer = generate_response(query, combined_context, project_info=project_info)
    return {"answer": answer}

def generate_greeting_response(query: str) -> str:
    """Generate a response for greetings and help requests"""
    query_lower = query.lower().strip()
    
    if query_lower in ["hi", "hello", "hey", "greetings", "hi there"]:
        return """Hello! I'm your Research Assistant. I can help you with:

- Answering questions about your research project
- Explaining research methodologies
- Analyzing data from your uploaded sources
- Providing guidance on research design

How can I assist with your research today?"""
    
    elif "help" in query_lower:
        return """I'd be happy to help! Here are some things I can do:

1. **Answer questions about your research** - Ask me about methodologies, designs, or concepts
2. **Analyze your sources** - Upload PDFs or documents, and I can answer questions about them
3. **Provide guidance** - I can suggest approaches for your research based on your project type
4. **Explain concepts** - Ask me to explain any research-related concept you're unclear about

Try asking a specific question about your research or your uploaded sources!"""
    
    else:
        return """Hello! I'm your Research Assistant ready to help with your research project. Feel free to ask me any question about research methods, your sources, or your project, and I'll do my best to assist you."""

@router.post("/chat", response_model=ResponseModel)
async def handle_chat(request: MessageRequest):
    """Handle chat messages"""
    message = request.message
    chat_history = request.chat_history
    enhanced_queries = request.enhanced_queries if hasattr(request, 'enhanced_queries') else True
    
    if not message:
        return {"answer": "Message is required"}
    
    # Check if it's a greeting or help request
    greeting_phrases = ["hi", "hello", "hey", "greetings", "hi there", "help", "help me", "i need help"]
    is_greeting = message.lower().strip() in greeting_phrases or message.lower().startswith("help with") or message.lower().startswith("how do i")
    
    if is_greeting:
        # Handle greetings and help requests directly without context
        greeting_response = generate_greeting_response(message)
        return {"answer": greeting_response}
    
    # Try to get context from the book for chat messages
    context_sources = []
    try:
        from app.services.book_service import get_context_from_book
        book_context, num_chunks = get_context_from_book(
            message, 
            5,
            use_enhanced_queries=enhanced_queries
        )
        if book_context:
            context_sources.append(f"book ({num_chunks} chunks)")
            context = book_context
        else:
            context = ""
    except ImportError:
        # Fallback to general query if book service doesn't exist
        context = get_context_from_query(
            message,
            use_enhanced_queries=enhanced_queries
        )
        if context:
            context_sources.append("general")
    
    # Log the sources used
    if context_sources:
        logger.info(f"Chat retrieved context from sources: {', '.join(context_sources)}")
    
    if not context:
        # If no context found, use a generic placeholder
        context = "I'll draw on my general knowledge to help with your research question."
    
    answer = generate_response(message, context, chat_history)
    return {"answer": answer}

@router.post("/ingest", response_model=Union[ResponseModel, PDFIngestionResponse])
async def ingest_pdf(
    file: UploadFile = File(...),
    project_id: Optional[int] = Form(None),
    user_id: Optional[str] = Form(None),
    process_type: str = Form("full"),  # Options: "full", "parse_only", "chunk_only", "embed_only"
    simple_mode: bool = Form(False),  # Parameter to mimic the old /upload behavior
    custom_document_name: Optional[str] = Form(None)  # New parameter for custom document name
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
        simple_mode: If True, returns a simple text response like the old deprecated /upload endpoint
        custom_document_name: Optional custom name to use for the document instead of the filename
    
    Returns:
        If simple_mode is True: A simple ResponseModel with a text answer
        Otherwise: A detailed PDFIngestionResponse with processing statistics
    """
    try:
        # Check if the file is a PDF
        if not file.filename.lower().endswith('.pdf'):
            raise HTTPException(status_code=400, detail="Only PDF files are supported")
        
        logger.info(f"Starting ingestion of file {file.filename} with simple_mode={simple_mode}, project_id={project_id} (type: {type(project_id)}), user_id={user_id}, custom_name={custom_document_name}")
        
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
            # Generate a summary first - since we need it for both the response and to store with the source
            # Parse the PDF to extract text for summary
            parser = PDFParser(temp_file_path)
            pdf_data = await parser.parse_pdf()
            
            # Generate a summary from the first few pages
            sample_text = ""
            for page in pdf_data.pages[:min(3, len(pdf_data.pages))]:
                sample_text += page.text + "\n\n"
            
            summary_prompt = f"""
            Analyze the following content from a PDF and provide a concise summary in 2-3 sentences:
            
            {sample_text[:5000]}  # Limiting content length for better focus
            """
            
            summary = generate_response(summary_prompt, sample_text)
            logger.info(f"Generated summary: {summary[:100]}...")
            
            # Initialize the ingestion service
            ingestion_service = PDFIngestionService()
            
            # Process the PDF based on the requested process type
            if process_type == "full":
                logger.info(f"Processing file {file.filename} with process_type={process_type}")
                
                # Pass the summary to the ingest_pdf method
                result = await ingestion_service.ingest_pdf(
                    temp_file_path, 
                    project_id, 
                    user_id,
                    custom_document_name=custom_document_name,
                    original_filename=file.filename,
                    summary=summary  # Pass the generated summary
                )
                logger.info(f"Ingestion result: {result}")
                
                # Get the display title that would be shown to the user
                display_title = result.get("ai_title") or custom_document_name or file.filename
                
                # If using simple mode, generate a simplified response
                if simple_mode:
                    logger.info("Using simple_mode response format")
                    
                    project_info = f" for project ID {project_id}" if project_id else ""
                    
                    # Determine the appropriate status message
                    if result["status"] == "error":
                        # More accurate message about what happened - database insert failed but document is still available
                        status_msg = "The source was added successfully"
                        chunks_info = f"but there was an issue storing the text for semantic search. The document is available but may not appear in search results."
                    else:
                        status_msg = "Successfully processed"
                        chunks_info = f"{result['chunks_embedded']} chunks of content were extracted and stored for future queries."
                    
                    return {
                        "answer": f"{status_msg} '{display_title}'{project_info}. {chunks_info}\n\nSummary: {summary}"
                    }
                
                # Always return the updated project sources if project_id is provided
                if project_id:
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

@router.post("/chat-with-project", response_model=ResponseModel)
async def chat_with_project(request: ChatWithProjectRequest):
    """
    Chat with a specific project
    """
    try:
        if not request.message:
            return {"output": "Please provide a message."}
            
        # Get project info for query reformulation
        project_id = request.project_id
        logger.info(f"Getting context for project {project_id}")
        
        project_response = supabase.table("projects").select("project_name, description, research_type, learning_objective").eq("project_id", project_id).execute()
        if not project_response.data:
            logger.warning(f"Project not found: {project_id}")
            project_info = ""
        else:
            project_data = project_response.data[0]
            project_info = f"Project: {project_data.get('project_name', 'Unknown')}\n"
            if project_data.get('description'):
                project_info += f"Description: {project_data.get('description')}\n"
            if project_data.get('research_type'):
                project_info += f"Research Type: {project_data.get('research_type')}\n"
            if project_data.get('learning_objective'):
                project_info += f"Learning Objective: {project_data.get('learning_objective')}\n"
            if request.message:
                project_info += f"Current Goal: {request.message}"
                
            logger.info(f"Project info: {project_info}")
        
        # Check if the selected document IDs exist in the database
        if request.selected_document_ids:
            # First, check what document IDs are available for this project
            # Using raw SQL query to get all distinct document_id and source values
            sql_query = f"""
            SELECT DISTINCT metadata->>'document_id' as doc_id, metadata->>'source' as source 
            FROM sources 
            WHERE project_id = {project_id} AND metadata IS NOT NULL
            """
            logger.info(f"Executing SQL query to check available documents: {sql_query}")
            
            # Execute the query
            available_docs_response = supabase.rpc('execute_sql', {'sql_query': sql_query}).execute()
            
            if available_docs_response.data:
                available_doc_ids = []
                available_sources = []
                
                # Parse the response
                for doc in available_docs_response.data:
                    if 'doc_id' in doc and doc['doc_id']:
                        available_doc_ids.append(doc['doc_id'])
                    if 'source' in doc and doc['source']:
                        available_sources.append(doc['source'])
                
                logger.info(f"Available document IDs for project {project_id}: {available_doc_ids}")
                logger.info(f"Available sources for project {project_id}: {available_sources}")
                
                # Check if any of the selected IDs match available documents
                matches_found = []
                for selected_id in request.selected_document_ids:
                    # Direct matches
                    if selected_id in available_doc_ids or selected_id in available_sources:
                        matches_found.append(selected_id)
                        continue
                        
                    # Partial matches
                    partial_match = False
                    for avail_id in available_doc_ids:
                        if (avail_id and selected_id in avail_id) or (avail_id and avail_id in selected_id):
                            matches_found.append(f"{selected_id} (matches {avail_id})")
                            partial_match = True
                            break
                            
                    for avail_source in available_sources:
                        if (avail_source and selected_id in avail_source) or (avail_source and avail_source in selected_id):
                            matches_found.append(f"{selected_id} (matches source {avail_source})")
                            partial_match = True
                            break
                            
                    if not partial_match:
                        logger.warning(f"No match found for document ID: {selected_id}")
                
                logger.info(f"Matched document IDs: {matches_found}")
            else:
                logger.warning(f"No available documents found for project {project_id}")
        
        # Get context for the query
        if request.selected_document_ids:
            logger.info(f"Getting context for project {project_id} with selected document IDs: {request.selected_document_ids}")
            project_context = get_context_for_project_with_selected_documents_intermediate(
                supabase,
                project_id,
                request.selected_document_ids,
                request.message,
                project_info
            )
            # Manually set num_chunks based on whether context was retrieved
            num_chunks = 0 if not project_context else 5  # This is temporary until function returns tuple
        else:
            logger.info(f"Getting context for all documents in project {project_id}")
            project_context = get_context_for_project_intermediate(
                supabase,
                project_id,
                request.message,
                project_info
            )
            # Manually set num_chunks based on whether context was retrieved
            num_chunks = 0 if not project_context else 5  # This is temporary until function returns tuple

        # Log context length for debugging
        context_length = len(project_context) if project_context else 0
        logger.info(f"Retrieved context of length {context_length} for project {project_id}")
        if not project_context:
            logger.warning(f"No context found for project {project_id}")
            # If no context was found, provide a generic response
            response = "I don't have enough information to answer your question. Please upload relevant documents to your project."
        else:
            logger.info(f"Generating AI response for project {project_id}")
            response = generate_response(request.message, project_context, request.project_id)

        return {"output": response}
    except Exception as e:
        logger.error(f"Error in chat_with_project: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error in chat_with_project: {str(e)}") 