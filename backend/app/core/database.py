from supabase import create_client, Client
from app.core.config import SUPABASE_URL, SUPABASE_KEY, logger

# Initialize Supabase client
try:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    logger.info("Supabase client initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize Supabase client: {e}")
    # Create a mock client for development/testing
    from unittest.mock import MagicMock
    supabase = MagicMock()
    logger.warning("Using mock Supabase client. Database features will not work.")

def retrieve_context(query_embedding: list, top_k: int = 5) -> list:
    """Retrieve relevant context from Supabase based on embedding similarity"""
    try:
        response = supabase.rpc("match_chunks", {
            "query_embedding": query_embedding,
            "match_count": top_k
        }).execute()
        
        if not response.data:
            logger.warning("No matching chunks found")
            return []
            
        return response.data
    except Exception as e:
        logger.error(f"Error retrieving context: {e}")
        return [] 