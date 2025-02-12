from typing import List
from .config import ChunkingConfig, CLASSIFY_PROMPT_PATH
import json
import requests
from .definitions import DEFINITIONS

def classify_chunk(text: str, config: ChunkingConfig) -> str:
    """
    Classifies a chunk of text using the Ollama model and research definitions.
    Returns one of: 'qualitative', 'quantitative', 'mixed', or 'general'.
    """
    # Read the prompt template
    with open(CLASSIFY_PROMPT_PATH, 'r') as f:
        prompt_template = f.read()
    
    # Format the prompt with definitions and text
    prompt = prompt_template.format(
        qualitative_def=DEFINITIONS['qualitative'],
        quantitative_def=DEFINITIONS['quantitative'],
        mixed_def=DEFINITIONS['mixed'],
        text=text
    )

    try:
        # Make request to Ollama
        response = requests.post(
            f"{config.ollama_base_url}/api/generate",
            json={
                "model": config.model,
                "prompt": prompt,
                "stream": False
            },
            timeout=30
        )
        
        response.raise_for_status()
        classification = response.json().get('response', '').strip().lower()
        
        # Validate the response is one of our expected classifications
        valid_classifications = {'qualitative', 'quantitative', 'mixed', 'general'}
        if classification in valid_classifications:
            return classification
        return 'general'  # Default if response is not valid
        
    except Exception as e:
        print(f"Error classifying chunk: {e}")
        return 'general'  # Default to general on error

def chunk_text_tokens(text: str, config: ChunkingConfig) -> List[dict]:
    """
    Splits the text by whitespace, grouping up to max_tokens tokens,
    then overlaps the last overlap_tokens tokens into the next chunk.
    """
    tokens = text.split()
    chunks = []
    start = 0

    while start < len(tokens):
        end = start + config.max_tokens
        chunk_str = " ".join(tokens[start:end])
        if chunk_str:
            # Classify each chunk right after creation
            classification = classify_chunk(chunk_str, config)
            chunks.append({
                "text": chunk_str,
                "classification": classification
            })
        # Move start to create overlap
        start = max(end - config.overlap_tokens, end)

    return chunks

def get_page_context(pages: List[dict], current_page_index: int) -> str:
    """
    Build textual context from surrounding pages
    """
    prev_text = pages[current_page_index - 1].get("text", "") if current_page_index > 0 else ""
    current_text = pages[current_page_index].get("text", "")
    next_text = pages[current_page_index + 1].get("text", "") if current_page_index < len(pages) - 1 else ""
    
    return "\n".join([prev_text, current_text, next_text]).strip() 