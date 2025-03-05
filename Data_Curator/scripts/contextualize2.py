import json
import requests
import logging
from typing import Dict, List

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("research_design_processing.log"),  # Log to a file
        logging.StreamHandler()  # Also log to console
    ]
)
logger = logging.getLogger(__name__)

# Assuming Ollama is running locally at http://localhost:11434/api/generate
OLLAMA_ENDPOINT = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "llama3.1:8b"  # Replace with your preferred model

# Load the JSON document
input_file = r"C:\Users\kenny\OneDrive\code\Research-Assistant\Data_Curator\output\chunked_examplename2.json"
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

def get_ollama_response(prompt: str) -> str:
    """
    Send prompt to Ollama and return the response.
    """
    logger.debug(f"Sending prompt to Ollama, length: {len(prompt)} characters")
    payload = {
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False
    }
    try:
        response = requests.post(OLLAMA_ENDPOINT, json=payload)
        response.raise_for_status()
        logger.debug("Ollama response received successfully")
        return response.json()["response"]
    except requests.RequestException as e:
        logger.error(f"Ollama API error: {e}")
        raise Exception(f"Ollama API error: {e}")

def contextualize_chunk(chunk: Dict, context: str) -> str:
    """
    Contextualize a single chunk using the provided prompt and Ollama.
    """
    chunk_id = f"chunk_{document['chunks'].index(chunk)}"
    raw_text = chunk["text"]
    logger.info(f"Contextualizing chunk: {raw_text[:50]}...")

    prompt = f"""
You are tasked with analyzing and enriching a text chunk using provided context. Your goal is to create a more informative version of the original text by integrating relevant information from the context while maintaining the original meaning.

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
6. Focus on providing a broad enhancement relevant to research design principles.

Your output should be formatted exactly as follows:

<chunk_id>{chunk_id}</chunk_id>
<raw_text>{raw_text}</raw_text>
<contextualized_chunk>
[Place your enriched version here. Integrate relevant context to enhance understanding while maintaining the original meaning.]
</contextualized_chunk>
"""
    response = get_ollama_response(prompt)
    logger.info(f"Chunk contextualized successfully: {raw_text[:50]}...")
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
        
        # Parse the enriched_response
        try:
            chunk_id = enriched_response.split("<chunk_id>")[1].split("</chunk_id>")[0]
            raw_text = enriched_response.split("<raw_text>")[1].split("</raw_text>")[0]
            contextualized_text = enriched_response.split("<contextualized_chunk>")[1].split("</contextualized_chunk>")[0].strip("[]")
            logger.debug(f"Parsed chunk {chunk_id} successfully")
        except IndexError as e:
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