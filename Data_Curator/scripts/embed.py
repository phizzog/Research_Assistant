import json
import requests
import logging
import time
import datetime
import os
from typing import Dict, List
from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure structured logging
current_time = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
log_filename = f"logs/embed_and_upload_{current_time}.log"

os.makedirs("logs", exist_ok=True)

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_filename),
        logging.StreamHandler()
    ]
)

perf_logger = logging.getLogger('performance')
perf_handler = logging.FileHandler(f"logs/performance_embed_{current_time}.log")
perf_handler.setFormatter(logging.Formatter('%(asctime)s - %(message)s'))
perf_logger.addHandler(perf_handler)
perf_logger.setLevel(logging.INFO)

logger = logging.getLogger(__name__)
logger.info(f"Starting embedding and upload run. Logs will be written to {log_filename}")

# Ollama configuration
OLLAMA_BASE_URL = 'http://localhost:11434'
OLLAMA_EMBED_ENDPOINT = f"{OLLAMA_BASE_URL}/api/embeddings"
OLLAMA_EMBED_MODEL = "nomic-embed-text:latest"

logger.info(f"Using Ollama embedding model: {OLLAMA_EMBED_MODEL} on local instance")

# Supabase configuration
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
SUPABASE_ENABLED = SUPABASE_URL is not None and SUPABASE_KEY is not None

if SUPABASE_ENABLED:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    logger.info("Supabase connection configured")
else:
    logger.error("Supabase connection not configured - SUPABASE_URL and SUPABASE_KEY required")
    raise ValueError("Supabase credentials missing in .env")

# Retry configuration
MAX_RETRIES = 3
COOLDOWN = 2  # seconds

# Load enriched JSON
input_file = "enriched_chunks.json"
logger.info(f"Loading enriched JSON from {input_file}")
try:
    with open(input_file, "r") as f:
        enriched_chunks = json.load(f)
    logger.info(f"Loaded {len(enriched_chunks)} enriched chunks successfully")
except Exception as e:
    logger.error(f"Failed to load enriched JSON: {e}")
    raise

def get_embeddings(text: str) -> List[float]:
    """
    Generate embeddings for the given text using nomic-embed-text:latest via Ollama.
    """
    logger.debug(f"Generating embedding for text: {text[:50]}...")
    start_time = time.time()

    payload = {
        "model": OLLAMA_EMBED_MODEL,
        "prompt": text
    }

    for attempt in range(MAX_RETRIES):
        try:
            if attempt > 0:
                time.sleep(COOLDOWN)
                perf_logger.info(f"Retry attempt {attempt + 1} after {COOLDOWN:.2f}s cooldown")

            response = requests.post(
                OLLAMA_EMBED_ENDPOINT,
                json=payload,
                timeout=30
            )
            response.raise_for_status()
            embedding = response.json().get("embedding", [])
            
            if not embedding:
                raise ValueError("No embedding returned from Ollama")

            end_time = time.time()
            duration = end_time - start_time
            perf_logger.info(f"Embedding generated in {duration:.2f}s. Model: {OLLAMA_EMBED_MODEL}")
            logger.debug(f"Embedding length: {len(embedding)}")
            return embedding

        except Exception as e:
            end_time = time.time()
            duration = end_time - start_time
            perf_logger.error(f"Embedding request failed in {duration:.2f}s on attempt {attempt + 1}: {str(e)}")
            if attempt == MAX_RETRIES - 1:
                logger.error("All retries failed for embedding", exc_info=True)
                return []

    return []

def clear_existing_data(book_title: str):
    """
    Clear existing chunks for the specified book title from Supabase.
    """
    try:
        supabase.table("chunks").delete().eq("metadata->>book_title", book_title).execute()
        logger.info(f"Cleared existing chunks for book: {book_title}")
    except Exception as e:
        logger.error(f"Failed to clear existing chunks: {e}")

def process_and_upload_chunks(
    chunks: List[Dict],
    book_title: str = "Research_Design_Qualitative,_Quantitative,_and_Mixed_Methods_Approaches",
    source_id: str = "book_001",
    output_file: str = "embedded_chunks.json"
):
    """
    Process each chunk to generate embeddings and upload to Supabase with raw_text.
    """
    # Clear existing data for this book
    clear_existing_data(book_title)
    
    total_chunks = len(chunks)
    logger.info(f"Starting processing of {total_chunks} chunks for embedding and upload")
    
    embedded_chunks = []

    for i, chunk in enumerate(chunks):
        logger.info(f"Processing chunk {i + 1}/{total_chunks}: {chunk['chunk_id']}")
        
        # Generate embedding for contextualized_text
        contextualized_text = chunk["contextualized_text"]
        embedding = get_embeddings(contextualized_text)
        
        if not embedding:
            logger.warning(f"Failed to generate embedding for chunk {chunk['chunk_id']}")
            continue
            
        chunk_with_embedding = chunk.copy()
        chunk_with_embedding["embedding"] = embedding
        embedded_chunks.append(chunk_with_embedding)
        
        # Upload to Supabase with both raw_text and contextualized_text
        try:
            chunk_data = {
                "chunk_id": chunk["chunk_id"],
                "raw_text": chunk["raw_text"],              # Added
                "contextualized_text": chunk["contextualized_text"],
                "metadata": {
                    "source_id": source_id,
                    "book_title": book_title,
                    "page_num": chunk["metadata"].get("page_num", 0),
                    "chunk_num": i + 1,
                    "total_chunks": total_chunks,
                    "section": chunk["metadata"].get("section", ""),
                    "subsection": chunk["metadata"].get("subsection", ""),
                    "topics": chunk["metadata"].get("topics", [])
                },
                "embedding": embedding
            }
            
            supabase.table("chunks").upsert(chunk_data).execute()
            logger.debug(f"Uploaded chunk {chunk['chunk_id']} to Supabase")
        except Exception as e:
            logger.error(f"Failed to upload chunk {chunk['chunk_id']} to Supabase: {e}")

    logger.info(f"Saving {len(embedded_chunks)} embedded chunks to {output_file}")
    with open(output_file, 'w') as f:
        json.dump(embedded_chunks, f, indent=2)
    logger.info(f"Embedded chunks saved to {output_file}")
    
    logger.info(f"Completed processing and uploading {total_chunks} chunks")
    return embedded_chunks

# Process and upload
try:
    embedded_chunks = process_and_upload_chunks(
        enriched_chunks,
        book_title="Research_Design_Qualitative,_Quantitative,_and_Mixed_Methods_Approaches",
        source_id="book_001",
        output_file="embedded_chunks.json"
    )
    print("Embeddings generated, data uploaded to Supabase, and saved locally successfully.")
except Exception as e:
    logger.error(f"Error during processing and uploading: {e}")
    raise