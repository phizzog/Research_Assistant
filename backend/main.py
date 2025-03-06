import os
from fastapi import FastAPI, Request, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from supabase import create_client, Client
from sentence_transformers import SentenceTransformer
import google.generativeai as genai
from dotenv import load_dotenv
import logging
from typing import Optional, List, Dict, Any
from pydantic import BaseModel

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI()

# CORS setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Supabase setup
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Embedding model
EMBEDDING_MODEL = "nomic-ai/nomic-embed-text-v1"
embedder = SentenceTransformer(EMBEDDING_MODEL, trust_remote_code=True)

# Alternative option (uncomment if the above doesn't work):
# EMBEDDING_MODEL = "all-MiniLM-L6-v2"  # A simpler model that doesn't require trust_remote_code
# embedder = SentenceTransformer(EMBEDDING_MODEL)

# Google Gemini setup
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=GEMINI_API_KEY)
gemini_model = genai.GenerativeModel('gemini-2.0-flash')  # Adjust model name as needed

# Pydantic models for request/response
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

# Retrieve context from Supabase
def retrieve_context(query: str, top_k: int = 5) -> str:
    try:
        query_embedding = embedder.encode(query).tolist()
        response = supabase.rpc("match_chunks", {
            "query_embedding": query_embedding,
            "match_count": top_k
        }).execute()
        
        if not response.data:
            logger.warning("No matching chunks found")
            return ""
            
        relevant_chunks = [item["contextualized_text"] for item in response.data]
        context = "\n\n".join(relevant_chunks)
        logger.info(f"Retrieved {len(relevant_chunks)} chunks for query: {query}")
        return context
    except Exception as e:
        logger.error(f"Error retrieving context: {e}")
        return ""

# Generate response with Gemini
def generate_response(query: str, context: str, chat_history: List[Dict[str, str]] = None) -> str:
    try:
        # Format chat history if provided
        history_text = ""
        if chat_history and len(chat_history) > 0:
            history_text = "Previous conversation:\n"
            for msg in chat_history:
                role = "User" if msg.get("role") == "user" else "Assistant"
                history_text += f"{role}: {msg.get('content')}\n"
            history_text += "\n"
        
        prompt = f"""
        ### Task:
        Answer the query using the provided context from a research design book. Provide a concise, accurate response based on the context.
        
        {history_text}
        
        ### Context:
        {context}
        
        ### Query:
        {query}
        """
        
        response = gemini_model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        logger.error(f"Gemini API error: {e}")
        return "Error generating response"

@app.post("/query", response_model=ResponseModel)
async def handle_query(request: QueryRequest):
    query = request.query
    top_k = request.top_k
    
    if not query:
        return {"answer": "Query is required"}
    
    context = retrieve_context(query, top_k)
    if not context:
        return {"answer": "No relevant context found. Please try a different query related to research design."}
    
    answer = generate_response(query, context)
    return {"answer": answer}

@app.post("/chat", response_model=ResponseModel)
async def handle_chat(request: MessageRequest):
    message = request.message
    chat_history = request.chat_history
    
    if not message:
        return {"answer": "Message is required"}
    
    context = retrieve_context(message)
    if not context:
        # If no context found, still try to answer based on general knowledge
        context = "No specific context found in the research design book."
    
    answer = generate_response(message, context, chat_history)
    return {"answer": answer}

@app.post("/upload", response_model=ResponseModel)
async def handle_file_upload(file: UploadFile = File(...)):
    try:
        contents = await file.read()
        file_content = contents.decode("utf-8")
        
        # Process the file content - for example, analyze it with Gemini
        prompt = f"""
        Analyze the following uploaded content and provide insights related to research design methodology:
        
        {file_content[:4000]}  # Limiting content length for API constraints
        """
        
        response = gemini_model.generate_content(prompt)
        return {"answer": response.text.strip()}
    except Exception as e:
        logger.error(f"Error processing file: {e}")
        return {"answer": f"Error processing file: {str(e)}"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 