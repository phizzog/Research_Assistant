import json
import logging
import os
import re
import datetime
import time
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from openai import OpenAI
from dotenv import load_dotenv
from pydantic import BaseModel, Field
import requests  # Add this import for making HTTP requests

# -----------------------------------------------------------------------------
# Load environment variables
# -----------------------------------------------------------------------------
load_dotenv()

# -----------------------------------------------------------------------------
# Configure structured logging (same style as original working script)
# -----------------------------------------------------------------------------
current_time = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
log_filename = f"logs/contextualize_{current_time}.log"

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        # File handler with detailed logging
        logging.FileHandler(log_filename),
        # Console handler with less verbose logging
        logging.StreamHandler()
    ]
)

# Performance logger for timing info
perf_logger = logging.getLogger('performance')
perf_handler = logging.FileHandler(f"logs/performance_{current_time}.log")
perf_handler.setFormatter(logging.Formatter('%(asctime)s - %(message)s'))
perf_logger.addHandler(perf_handler)
perf_logger.setLevel(logging.INFO)

logger = logging.getLogger(__name__)
logger.info(f"Starting new processing run. Logs will be written to {log_filename}")

# Update Ollama base URL (removed /api since we'll add it in the endpoint)
OLLAMA_BASE_URL = 'http://192.168.10.3:11436'

# -----------------------------------------------------------------------------
# Configure OpenAI client to use local Ollama
# -----------------------------------------------------------------------------
client = OpenAI(
    base_url='http://192.168.10.3:11436/v1',  # Your Ollama endpoint
    api_key='ollama'
)

logger.info(f"Using Ollama model: gemma:7b")

# -----------------------------------------------------------------------------
# Dataclass config
# -----------------------------------------------------------------------------
@dataclass
class ChunkingConfig:
    context_pages: int = 5          # not specifically used here, but kept if needed
    max_retries: int = 2
    cooldown: float = 0.1
    model: str = "gemma:7b"
    max_tokens: int = 300          # for token-based chunking
    overlap_tokens: int = 50       # overlap for token-based chunking

# -----------------------------------------------------------------------------
# Utility: Tag extraction
# -----------------------------------------------------------------------------
def extract_tag(text: str, tag: str) -> str:
    """
    Extract the contents of <tag>...</tag> from text.
    If not found, returns "".
    """
    pattern = fr"<{tag}>(.*?)</{tag}>"
    match = re.search(pattern, text, re.DOTALL)
    if match:
        return match.group(1).strip()
    return ""

# -----------------------------------------------------------------------------
# Utility: Get raw response from Ollama (without JSON parsing)
# -----------------------------------------------------------------------------
def get_raw_response(prompt: str, config: ChunkingConfig) -> str:
    """
    Sends a prompt to Ollama using its native API and returns the complete text response.
    """
    logger.debug("=" * 80)
    logger.debug("SENDING PROMPT TO OLLAMA (raw):")
    logger.debug(f"Prompt:\n{prompt}")

    start_time = time.time()

    # Update payload to remove :latest suffix from model name
    payload = {
        "model": config.model,  # Remove :latest suffix
        "prompt": prompt,
        "stream": False
    }

    for attempt in range(config.max_retries):
        try:
            if attempt > 0:
                time.sleep(config.cooldown)
                perf_logger.info(f"Retry attempt {attempt + 1} after {config.cooldown:.2f}s cooldown")

            # Update endpoint to include /api/generate
            response = requests.post(
                f"{OLLAMA_BASE_URL}/api/generate",
                json=payload,
                timeout=30
            )
            
            response.raise_for_status()
            response_data = response.json()
            
            # Extract just the response text from Ollama's response
            response_text = response_data.get('response', '')
            
            # Add logging for additional Ollama metrics
            perf_logger.info(
                f"Ollama metrics - "
                f"Total duration: {response_data.get('total_duration', 0)/1e9:.2f}s, "
                f"Eval tokens: {response_data.get('eval_count', 0)}"
            )

            end_time = time.time()
            duration = end_time - start_time

            perf_logger.info(
                f"Ollama request completed in {duration:.2f}s. "
                f"Model: {config.model}"
            )

            logger.debug("RAW OLLAMA RESPONSE:")
            logger.debug(response_text)

            return response_text

        except Exception as e:
            end_time = time.time()
            duration = end_time - start_time
            perf_logger.error(f"Request failed in {duration:.2f}s on attempt {attempt + 1}: {str(e)}")
            if attempt == config.max_retries - 1:
                logger.error("All retries failed", exc_info=True)
                return ""

    return ""

# -----------------------------------------------------------------------------
# Chunk-based contextualization: Generate enriched chunk
# -----------------------------------------------------------------------------
def generate_chunk_context(
    chunk_text: str,
    context: str,
    chunk_id: str,
    config: ChunkingConfig
) -> dict:
    """
    Creates a prompt to enrich the chunk_text with the context.
    Returns a dictionary containing:
    {
        "chunk_id": str,
        "raw_text": str,
        "contextualized_chunk": str
    }
    """
    prompt = f"""You will analyze this text chunk using the provided context and create an enriched version.

IMPORTANT: Your response must be formatted exactly as shown below, with your generated content placed inside the XML tags:

<chunk_id>{chunk_id}</chunk_id>
<raw_text>{chunk_text}</raw_text>
<contextualized_chunk>
[Place your enriched version here. Integrate relevant context to enhance understanding while maintaining the original meaning.]
</contextualized_chunk>

Context for reference:
{context}

Remember: Place your enriched version INSIDE the contextualized_chunk tags. Do not modify the other tags."""

    response_text = get_raw_response(prompt, config)

    extracted_chunk_id = extract_tag(response_text, "chunk_id")
    extracted_raw_text = extract_tag(response_text, "raw_text")
    extracted_contextualized_chunk = extract_tag(response_text, "contextualized_chunk")

    return {
        "chunk_id": extracted_chunk_id,
        "raw_text": extracted_raw_text,
        "contextualized_chunk": extracted_contextualized_chunk
    }

# -----------------------------------------------------------------------------
# Table-based contextualization: Generate enriched table description
# -----------------------------------------------------------------------------
def generate_table_context_with_tags(
    table_data: List[List[str]],
    context: str,
    table_id: str,
    config: ChunkingConfig
) -> dict:
    """
    Creates a prompt to enrich table_data with the context.
    Returns a dictionary containing:
    {
        "table_id": str,
        "raw_table": str,
        "contextualized_table": str
    }
    """
    # Convert table data to JSON string for embedding in prompt
    table_json = json.dumps(table_data)

    prompt = f"""You will analyze this table data using the provided context and create an enriched description.

IMPORTANT: Your response must be formatted exactly as shown below, with your generated content placed inside the XML tags:

<table_id>{table_id}</table_id>
<raw_table>{table_json}</raw_table>
<contextualized_table>
[Place your enriched description here. Explain the table's content in detail, incorporating relevant context to enhance understanding.]
</contextualized_table>

Context for reference:
{context}

Remember: Place your enriched description INSIDE the contextualized_table tags. Do not modify the other tags."""

    response_text = get_raw_response(prompt, config)

    extracted_table_id = extract_tag(response_text, "table_id")
    extracted_raw_table = extract_tag(response_text, "raw_table")
    extracted_contextualized_table = extract_tag(response_text, "contextualized_table")

    return {
        "table_id": extracted_table_id,
        "raw_table": extracted_raw_table,
        "contextualized_table": extracted_contextualized_table
    }

# -----------------------------------------------------------------------------
# Token-based chunking (the new approach)
# -----------------------------------------------------------------------------
def chunk_text_tokens(text: str, max_tokens: int = 300, overlap_tokens: int = 50) -> List[str]:
    """
    Splits the text by whitespace, grouping up to max_tokens tokens,
    then overlaps the last overlap_tokens tokens into the next chunk.
    """
    tokens = text.split()
    chunks = []
    start = 0

    while start < len(tokens):
        end = start + max_tokens
        chunk = " ".join(tokens[start:end])
        if chunk:
            chunks.append(chunk)
        # Move start to create overlap
        start = max(end - overlap_tokens, end)

    return chunks

# -----------------------------------------------------------------------------
# Main transform function
# -----------------------------------------------------------------------------
def transform_document(input_path: str, output_path: str):
    start_time = datetime.datetime.now()
    logger.info(f"Starting document transformation: {input_path}")
    perf_logger.info(f"Transform started at: {start_time}")

    try:
        # Load input JSON
        with open(input_path, 'r') as f:
            original_data = json.load(f)

        # Configuration
        config = ChunkingConfig()
        logger.info(f"Using config: {config}")

        document_metadata = original_data.get("document", {})
        pages = original_data.get("pages", [])

        new_pages = []

        # ---------------------------------------------------------------------
        # For each page, gather context from prev/current/next page
        # ---------------------------------------------------------------------
        total_chunks_count = 0
        for i, page in enumerate(pages):
            page_id = page.get("page_id", f"page_{i}")
            pdf_title = page.get("pdf_title", "")
            current_text = page.get("text", "")

            # Build textual context from surrounding pages
            prev_text = pages[i - 1].get("text", "") if i > 0 else ""
            next_text = pages[i + 1].get("text", "") if i < len(pages) - 1 else ""
            context = "\n".join([prev_text, current_text, next_text]).strip()

            # -----------------------------------------------------------------
            # 1) Chunk the current page text (token-based)
            # -----------------------------------------------------------------
            chunking_start = datetime.datetime.now()
            text_chunks = chunk_text_tokens(
                current_text,
                max_tokens=config.max_tokens,
                overlap_tokens=config.overlap_tokens
            )
            chunking_end = datetime.datetime.now()
            chunking_duration = (chunking_end - chunking_start).total_seconds()
            perf_logger.info(
                f"Page {i+1}/{len(pages)} - chunking completed in {chunking_duration:.2f}s, "
                f"generated {len(text_chunks)} chunks."
            )

            # -----------------------------------------------------------------
            # 2) Enrich each chunk
            # -----------------------------------------------------------------
            new_chunks = []
            for idx, chunk in enumerate(text_chunks, start=1):
                chunk_id = f"{page_id}_chunk_{idx}"
                logger.info(f"Processing chunk {idx}/{len(text_chunks)} on page {page_id}")

                # Time the per-chunk call
                chunk_process_start = datetime.datetime.now()
                enriched_chunk = generate_chunk_context(chunk, context, chunk_id, config)
                chunk_process_end = datetime.datetime.now()

                chunk_duration = (chunk_process_end - chunk_process_start).total_seconds()
                perf_logger.info(
                    f"Chunk {idx}/{len(text_chunks)} on page {page_id} processed in {chunk_duration:.2f}s"
                )

                new_chunks.append(enriched_chunk)

            total_chunks_count += len(new_chunks)

            # -----------------------------------------------------------------
            # 3) Enrich each table if tables exist
            # -----------------------------------------------------------------
            new_tables = []
            for t_i, table in enumerate(page.get("tables", []), start=1):
                table_id = table.get("table_id", f"{page_id}_table_{t_i}")
                table_data = table.get("data", [])

                logger.info(f"Processing table {t_i} on page {page_id}")
                table_process_start = datetime.datetime.now()
                enriched_table = generate_table_context_with_tags(table_data, context, table_id, config)
                table_process_end = datetime.datetime.now()

                table_duration = (table_process_end - table_process_start).total_seconds()
                perf_logger.info(
                    f"Table {t_i} on page {page_id} processed in {table_duration:.2f}s"
                )

                new_tables.append(enriched_table)

            new_page = {
                "page_id": page_id,
                "pdf_title": pdf_title,
                "text": current_text,
                # Original text plus newly enriched chunks
                "text_chunks": new_chunks,
                "tables": new_tables
            }
            new_pages.append(new_page)

        # ---------------------------------------------------------------------
        # Prepare final output
        # ---------------------------------------------------------------------
        output_data = {
            "document": document_metadata,
            "pages": new_pages,
            "contextual_relationships": {}
        }

        # Write output JSON
        with open(output_path, 'w') as f:
            json.dump(output_data, f, indent=2)

        end_time = datetime.datetime.now()
        total_duration = (end_time - start_time).total_seconds()
        logger.info(
            f"Transformation complete. Processed {len(new_pages)} pages and {total_chunks_count} chunks "
            f"in {total_duration:.2f} seconds."
        )
        perf_logger.info(f"Total processing time: {total_duration:.2f} seconds")

    except Exception as e:
        logger.error("Document transformation failed", exc_info=True)
        raise

# -----------------------------------------------------------------------------
# If running as a standalone script
# -----------------------------------------------------------------------------
if __name__ == "__main__":
    try:
        transform_document("input/test.json", "output/contextualized_output.json")
    except Exception as e:
        logger.error(f"Failed to process document: {str(e)}")
