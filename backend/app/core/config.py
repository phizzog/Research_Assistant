import os
from dotenv import load_dotenv
import logging
from loguru import logger

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# API settings
API_HOST = "0.0.0.0"
API_PORT = 8000
CORS_ORIGINS = ["http://localhost:3000"]  # Frontend URL

# Supabase settings
SUPABASE_URL = os.getenv("SUPABASE_URL")
if not SUPABASE_URL:
    logger.warning("SUPABASE_URL environment variable not set. Some features may not work correctly.")
    SUPABASE_URL = "https://example.supabase.co"  # Placeholder value

SUPABASE_KEY = os.getenv("SUPABASE_KEY")
if not SUPABASE_KEY:
    logger.warning("SUPABASE_KEY environment variable not set. Some features may not work correctly.")
    SUPABASE_KEY = "placeholder_key"  # Placeholder value

# Embedding model settings
EMBEDDING_MODEL = "nomic-ai/nomic-embed-text-v1"
USE_TRUST_REMOTE_CODE = True

# Alternative embedding model (uncomment if the above doesn't work)
# EMBEDDING_MODEL = "all-MiniLM-L6-v2"
# USE_TRUST_REMOTE_CODE = False

# Google Gemini settings
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    logger.warning("GEMINI_API_KEY environment variable not set. AI features will not work correctly.")
    GEMINI_API_KEY = "placeholder_key"  # Placeholder value

GEMINI_MODEL = "gemini-2.0-flash"  # Adjust model name as needed 