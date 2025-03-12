from sentence_transformers import SentenceTransformer
import google.generativeai as genai
from typing import List, Dict
from app.core.config import (
    EMBEDDING_MODEL, 
    USE_TRUST_REMOTE_CODE, 
    GEMINI_API_KEY, 
    GEMINI_MODEL,
    logger
)

# Initialize embedding model
try:
    embedder = SentenceTransformer(EMBEDDING_MODEL, trust_remote_code=USE_TRUST_REMOTE_CODE)
    logger.info(f"Embedding model {EMBEDDING_MODEL} initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize embedding model: {e}")
    # Create a mock embedder for development/testing
    from unittest.mock import MagicMock
    embedder = MagicMock()
    embedder.encode.return_value = [0.0] * 768  # Return a vector of zeros
    logger.warning("Using mock embedding model. Vector search features will not work correctly.")

# Initialize Gemini model
try:
    genai.configure(api_key=GEMINI_API_KEY)
    gemini_model = genai.GenerativeModel(GEMINI_MODEL)
    logger.info(f"Gemini model {GEMINI_MODEL} initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize Gemini model: {e}")
    # Create a mock Gemini model for development/testing
    from unittest.mock import MagicMock
    gemini_model = MagicMock()
    gemini_model.generate_content.return_value.text = "This is a mock response. The Gemini API is not available."
    logger.warning("Using mock Gemini model. AI responses will not be accurate.")

def generate_embeddings(text: str) -> List[float]:
    """Generate embeddings for a given text"""
    try:
        return embedder.encode(text).tolist()
    except Exception as e:
        logger.error(f"Error generating embeddings: {e}")
        # Return a vector of zeros as fallback
        return [0.0] * 768

def generate_response(query: str, context: str, chat_history: List[Dict[str, str]] = None) -> str:
    """Generate a response using Gemini model"""
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
        return f"Error generating response: {str(e)}" 