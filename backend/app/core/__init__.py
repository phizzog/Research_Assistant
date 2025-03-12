from app.core.config import (
    API_HOST,
    API_PORT,
    CORS_ORIGINS,
    logger
)
from app.core.database import supabase, retrieve_context
from app.core.ai import generate_embeddings, generate_response
