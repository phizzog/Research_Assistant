import json
import requests
import logging
import time
import datetime
import os
import re
from typing import Dict, List, Optional
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure structured logging
current_time = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
log_filename = f"logs/contextualize3_{current_time}.log"

# Ensure logs directory exists
os.makedirs("logs", exist_ok=True)

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

# Update Ollama base URL and endpoint
OLLAMA_BASE_URL = 'http://192.168.10.3:11436'
OLLAMA_ENDPOINT = f"{OLLAMA_BASE_URL}/api/generate"
OLLAMA_MODEL = "llama3.1:8b"  # Using the same model as in contextualize.py

# Configure OpenAI client to use local Ollama
client = OpenAI(
    base_url=f'{OLLAMA_BASE_URL}/v1',  # Ollama endpoint
    api_key='ollama'
)

logger.info(f"Using Ollama model for contextualization: {OLLAMA_MODEL}")

# Configuration for retries
MAX_RETRIES = 3
COOLDOWN = 2  # seconds

# Load the JSON document
input_file = r"/Users/ksnyder/Research-Assistant/Data_Curator/output/chunked_test.json"
logger.info(f"Loading JSON document from {input_file}")
try:
    with open(input_file, "r") as f:
        document = json.load(f)
    logger.info("JSON document loaded successfully")
except Exception as e:
    logger.error(f"Failed to load JSON document: {e}")
    raise

def determine_context(chunk: Dict, document: List[Dict]) -> str:
    """
    Dynamically determine relevant context for a chunk based on its metadata and content.
    """
    metadata = chunk["metadata"]
    raw_text = chunk["text"]
    logger.debug(f"Determining context for chunk: {raw_text[:50]}...")

    # Base context from the book's preface for general background
    base_context_chunks = [c["text"] for c in document if c["metadata"]["section"] == "PREFACE"]
    base_context = "\n".join(base_context_chunks)

    # Add context based on part (e.g., Part I or Part II)
    part_context = ""
    if metadata["part"]:
        part_context_chunks = [
            c["text"] for c in document 
            if c["metadata"]["part"] == metadata["part"] and c["text"] != raw_text
        ]
        part_context = "\n".join(part_context_chunks[:3])  # Limit to 3 chunks for brevity

    # Add chapter-specific context if available
    chapter_context = ""
    if metadata["chapter"]:
        chapter_context_chunks = [
            c["text"] for c in document 
            if c["metadata"]["chapter"] == metadata["chapter"] and c["text"] != raw_text
        ]
        chapter_context = "\n".join(chapter_context_chunks[:2])  # Limit to 2 chunks

    # Combine contexts
    full_context = f"{base_context}\n\n{part_context}\n\n{chapter_context}".strip()
    logger.debug(f"Context determined, length: {len(full_context)} characters")
    return full_context

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

def get_ollama_response(prompt: str) -> str:
    """
    Sends a prompt to Ollama using its native API and returns the complete text response.
    Includes retry logic and performance logging.
    """
    logger.debug("=" * 80)
    logger.debug("SENDING PROMPT TO OLLAMA:")
    logger.debug(f"Prompt:\n{prompt}")

    start_time = time.time()

    payload = {
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False
    }

    for attempt in range(MAX_RETRIES):
        try:
            if attempt > 0:
                time.sleep(COOLDOWN)
                perf_logger.info(f"Retry attempt {attempt + 1} after {COOLDOWN:.2f}s cooldown")

            response = requests.post(
                OLLAMA_ENDPOINT,
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
                f"Model: {OLLAMA_MODEL}"
            )

            logger.debug("OLLAMA RESPONSE:")
            logger.debug(response_text)

            return response_text

        except Exception as e:
            end_time = time.time()
            duration = end_time - start_time
            perf_logger.error(f"Request failed in {duration:.2f}s on attempt {attempt + 1}: {str(e)}")
            if attempt == MAX_RETRIES - 1:
                logger.error("All retries failed", exc_info=True)
                return ""

    return ""

def get_openai_completion(prompt: str) -> Optional[str]:
    """
    Uses the OpenAI client to get a completion from Ollama.
    This is an alternative to the direct API call method.
    """
    logger.debug("=" * 80)
    logger.debug("SENDING PROMPT TO OLLAMA (via OpenAI client):")
    logger.debug(f"Prompt:\n{prompt}")

    start_time = time.time()

    for attempt in range(MAX_RETRIES):
        try:
            if attempt > 0:
                time.sleep(COOLDOWN)
                perf_logger.info(f"Retry attempt {attempt + 1} after {COOLDOWN:.2f}s cooldown")

            response = client.completions.create(
                model=OLLAMA_MODEL,
                prompt=prompt,
                max_tokens=2048,
                temperature=0.7,
                stream=False
            )
            
            response_text = response.choices[0].text
            
            end_time = time.time()
            duration = end_time - start_time

            perf_logger.info(
                f"OpenAI client request completed in {duration:.2f}s. "
                f"Model: {OLLAMA_MODEL}"
            )

            logger.debug("OLLAMA RESPONSE (via OpenAI client):")
            logger.debug(response_text)

            return response_text

        except Exception as e:
            end_time = time.time()
            duration = end_time - start_time
            perf_logger.error(f"OpenAI client request failed in {duration:.2f}s on attempt {attempt + 1}: {str(e)}")
            if attempt == MAX_RETRIES - 1:
                logger.error("All retries failed", exc_info=True)
                return None

    return None

def contextualize_chunk(chunk: Dict, context: str) -> str:
    """
    Contextualize a single chunk using the provided prompt and Ollama, including the type of research in the enriched text.
    """
    chunk_id = f"chunk_{document['chunks'].index(chunk)}"
    raw_text = chunk["text"]
    logger.info(f"Contextualizing chunk: {raw_text[:50]}...")

    prompt = f"""
You are tasked with analyzing and enriching a text chunk using provided context. Your goal is to create a more informative version of the original text by integrating relevant information from the context while maintaining the original meaning. In your enriched version, explicitly state whether this chunk pertains to qualitative, quantitative, or mixed methods research—or general research design principles if it does not specifically fit into one of those categories—based on its content and the provided context.

First, review the following context carefully. This information will help you understand the broader topic and enrich the text chunk:

<context>
{context}
</context>

Now, you will be given a chunk of text to analyze and enrich. Here are the details:

<chunk_id>{chunk_id}</chunk_id>

<raw_text>
{raw_text}
</raw_text>

To create the contextualized chunk:
1. Carefully read the raw text and understand its main points.
2. Identify key concepts, terms, or ideas in the raw text that could benefit from additional context.
3. Refer back to the provided context and find relevant information that can enhance the understanding of the raw_text.
4. Integrate this contextual information into the raw_text, expanding on important points, clarifying concepts, or providing background information as needed.
5. Ensure that the original meaning and intent of the raw_text are preserved while adding depth and clarity.
6. In the enriched text, include a statement specifying the type of research (qualitative, quantitative, mixed methods, or general research design principles) this chunk relates to, inferred from its content and context.
7. Focus on providing a broad enhancement relevant to research design principles, tailored to the inferred research type.

Your output should be formatted exactly as follows:

<chunk_id>{chunk_id}</chunk_id>
<raw_text>{raw_text}</raw_text>
<contextualized_chunk>
[Place your enriched version here. Integrate relevant context to enhance understanding while maintaining the original meaning, and state the type of research involved.]
</contextualized_chunk>
"""
    # Try using the OpenAI client first
    try:
        response = get_openai_completion(prompt)
        if response:
            logger.info(f"Chunk contextualized successfully using OpenAI client: {raw_text[:50]}...")
            return response
    except Exception as e:
        logger.warning(f"OpenAI client failed, falling back to direct API: {str(e)}")
    
    # Fall back to direct API call if OpenAI client fails
    response = get_ollama_response(prompt)
    logger.info(f"Chunk contextualized successfully using direct API: {raw_text[:50]}...")
    return response

def process_chunks(document: Dict) -> List[Dict]:
    """
    Process all chunks: contextualize and parse the enriched response.
    """
    enriched_chunks = []
    total_chunks = len(document["chunks"])
    logger.info(f"Starting processing of {total_chunks} chunks")

    for i, chunk in enumerate(document["chunks"]):
        logger.info(f"Processing chunk {i + 1}/{total_chunks}")
        
        # Determine context and contextualize
        context = determine_context(chunk, document["chunks"])
        enriched_response = contextualize_chunk(chunk, context)
        
        # Parse the enriched_response using the extract_tag utility
        try:
            chunk_id = extract_tag(enriched_response, "chunk_id")
            raw_text = extract_tag(enriched_response, "raw_text")
            contextualized_text = extract_tag(enriched_response, "contextualized_chunk").strip("[]")
            
            if not chunk_id or not raw_text or not contextualized_text:
                raise ValueError("Failed to extract required tags from response")
                
            logger.debug(f"Parsed chunk {chunk_id} successfully")
        except Exception as e:
            logger.warning(f"Error parsing enriched response for chunk: {chunk['text'][:50]}... - {e}")
            chunk_id = f"chunk_{document['chunks'].index(chunk)}"
            raw_text = chunk["text"]
            contextualized_text = "Error parsing enriched response"
        
        # Structure the enriched chunk
        enriched_chunk = {
            "chunk_id": chunk_id,
            "raw_text": raw_text,
            "contextualized_text": contextualized_text,
            "metadata": chunk["metadata"]
        }
        enriched_chunks.append(enriched_chunk)
    
    logger.info(f"Completed processing {total_chunks} chunks")
    return enriched_chunks

# Process the chunks
try:
    enriched_data = process_chunks(document)
except Exception as e:
    logger.error(f"Error during chunk processing: {e}")
    raise

# Save to file
output_file = "enriched_chunks.json"
logger.info(f"Saving enriched chunks to {output_file}")
try:
    with open(output_file, "w") as f:
        json.dump(enriched_data, f, indent=2)
    logger.info(f"Enriched chunks saved successfully to {output_file}")
except Exception as e:
    logger.error(f"Failed to save enriched chunks: {e}")
    raise

print("Chunks enriched, parsed, and saved to 'enriched_chunks.json'.")

# Optional: Supabase integration
# Uncomment and configure if you want to upload to Supabase
"""
from supabase import create_client, Client

supabase_url = "your-supabase-url"
supabase_key = "your-supabase-key"
supabase: Client = create_client(supabase_url, supabase_key)

logger.info("Uploading data to Supabase")
for chunk in enriched_data:
    data = {
        "chunk_id": chunk["chunk_id"],
        "raw_text": chunk["raw_text"],
        "contextualized_text": chunk["contextualized_text"],
        "metadata": chunk["metadata"]
    }
    try:
        supabase.table("chunks").insert(data).execute()
        logger.debug(f"Uploaded chunk {chunk['chunk_id']} to Supabase")
    except Exception as e:
        logger.error(f"Failed to upload chunk {chunk['chunk_id']} to Supabase: {e}")

logger.info("Data uploaded to Supabase successfully")
print("Data uploaded to Supabase.")
"""