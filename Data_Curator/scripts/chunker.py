from typing import List, Dict, Union, Any
from .config import ChunkingConfig, CLASSIFY_PROMPT_PATH
import json
import requests
from .definitions import DEFINITIONS
import logging

def classify_chunk(text: str, context: str, config: ChunkingConfig) -> str:
    """
    Classifies a chunk of text using the Ollama model and research definitions.
    Returns one of: 'qualitative', 'quantitative', 'mixed', or 'general'.
    
    Args:
        text: The text chunk to classify
        context: Surrounding context from adjacent chunks/pages
        config: Configuration settings
    """
    logger = logging.getLogger(__name__)
    logger.info(f"Starting classification of chunk with {len(text.split())} words")
    
    # Load the prompt template from file
    try:
        with open(CLASSIFY_PROMPT_PATH, 'r', encoding='utf-8') as f:
            prompt_template = f.read()
    except Exception as e:
        logger.error(f"Error loading classification prompt template: {e}")
        return 'general'  # Default if we can't load the prompt
    
    # Format the prompt with the required values
    prompt = prompt_template.format(
        qualitative_def=DEFINITIONS['qualitative'],
        quantitative_def=DEFINITIONS['quantitative'],
        mixed_def=DEFINITIONS['mixed'],
        text=text,
        context=context
    )

    try:
        logger.info(f"Sending classification request to Ollama at {config.ollama_base_url}")
        # Make request to Ollama with a longer timeout
        response = requests.post(
            f"{config.ollama_base_url}/api/generate",
            json={
                "model": config.model,
                "prompt": prompt,
                "stream": False
            },
            timeout=60  # Increased timeout to 60 seconds
        )
        
        response.raise_for_status()
        response_text = response.json().get('response', '').strip()
        logger.info(f"Received classification response from Ollama ({len(response_text)} chars)")
        
        # Extract classification from the XML tags
        classification = 'general'  # Default value
        
        # Look for classification tag
        if '<classification>' in response_text and '</classification>' in response_text:
            start_tag = '<classification>'
            end_tag = '</classification>'
            start_idx = response_text.find(start_tag) + len(start_tag)
            end_idx = response_text.find(end_tag)
            if start_idx != -1 and end_idx != -1:
                classification = response_text[start_idx:end_idx].strip().lower()
                logger.info(f"Extracted classification: {classification}")
        else:
            logger.warning("Classification tags not found in response")
        
        # Validate the response is one of our expected classifications
        valid_classifications = {'qualitative', 'quantitative', 'mixed', 'general'}
        if classification in valid_classifications:
            return classification
        
        logger.warning(f"Invalid classification '{classification}', defaulting to 'general'")
        return 'general'  # Default if response is not valid
        
    except requests.exceptions.Timeout:
        logger.error(f"Timeout connecting to Ollama API at {config.ollama_base_url}")
        return 'general'  # Default to general on timeout
    except requests.exceptions.ConnectionError:
        logger.error(f"Connection error to Ollama API at {config.ollama_base_url}")
        return 'general'  # Default to general on connection error
    except Exception as e:
        logger.error(f"Error classifying chunk: {e}", exc_info=True)
        return 'general'  # Default to general on error

def process_table_data(table: Dict[str, Any], config: ChunkingConfig) -> List[dict]:
    """
    Process table data into classifiable chunks while preserving table context.
    
    Args:
        table: Dictionary containing table data with 'table_id' and 'data' fields
        config: Configuration settings
    """
    chunks = []
    if not table.get('data'):
        return chunks
        
    # Convert table data to string representation
    table_text = "\n".join([" | ".join(row) for row in table['data']])
    
    # Add table identifier context
    table_context = f"Table {table['table_id']}: "
    
    # Process table text into chunks
    tokens = table_text.split()
    start = 0
    
    while start < len(tokens):
        end = start + config.max_tokens
        chunk_str = " ".join(tokens[start:end])
        if chunk_str:
            context_start = max(0, start - config.overlap_tokens)
            context_end = min(len(tokens), end + config.overlap_tokens)
            context_str = table_context + " ".join(tokens[context_start:context_end])
            
            classification = classify_chunk(chunk_str, context_str, config)
            chunks.append({
                "text": chunk_str,
                "classification": classification,
                "source": "table",
                "table_id": table['table_id']
            })
        start = max(end - config.overlap_tokens, end)
    
    return chunks

def process_page(page: Dict[str, Any], config: ChunkingConfig) -> List[dict]:
    """
    Process a page including both its text content and tables.
    
    Args:
        page: Dictionary containing page data according to schema
        config: Configuration settings
    """
    chunks = []
    
    # Process main text content
    if page.get('text'):
        text_chunks = chunk_text_tokens(page['text'], config)
        for chunk in text_chunks:
            chunk['source'] = 'text'
            chunk['page_id'] = page['page_id']
        chunks.extend(text_chunks)
    
    # Process tables if present
    if page.get('tables'):
        for table in page['tables']:
            table_chunks = process_table_data(table, config)
            for chunk in table_chunks:
                chunk['page_id'] = page['page_id']
            chunks.extend(table_chunks)
    
    return chunks

def get_page_context(pages: List[dict], current_page_index: int) -> str:
    """
    Build textual context from surrounding pages, including both text and table content.
    """
    def extract_page_content(page: dict) -> str:
        content_parts = []
        if page.get('text'):
            content_parts.append(page['text'])
        if page.get('tables'):
            for table in page['tables']:
                if table.get('data'):
                    table_text = f"Table {table['table_id']}:\n"
                    table_text += "\n".join([" | ".join(row) for row in table['data']])
                    content_parts.append(table_text)
        return "\n".join(content_parts)
    
    prev_text = extract_page_content(pages[current_page_index - 1]) if current_page_index > 0 else ""
    current_text = extract_page_content(pages[current_page_index])
    next_text = extract_page_content(pages[current_page_index + 1]) if current_page_index < len(pages) - 1 else ""
    
    return "\n".join([prev_text, current_text, next_text]).strip()

def chunk_text_tokens(text: str, config: ChunkingConfig) -> List[dict]:
    """
    Splits the text into chunks, trying to preserve sentence boundaries when possible,
    and ensuring chunks are of appropriate size with proper overlap.
    """
    import re
    
    # Split text into sentences
    sentence_endings = r'(?<=[.!?])\s+'
    sentences = re.split(sentence_endings, text)
    
    chunks = []
    current_chunk = []
    current_token_count = 0
    
    for sentence in sentences:
        # Approximate token count by words (not perfect but better than nothing)
        sentence_tokens = len(sentence.split())
        
        # If adding this sentence would exceed max_tokens, finalize the current chunk
        if current_token_count + sentence_tokens > config.max_tokens and current_token_count > 0:
            chunk_str = " ".join(current_chunk)
            
            # Get surrounding context
            chunk_tokens = chunk_str.split()
            context_tokens = text.split()
            
            # Find position of chunk in the full text
            chunk_start = 0
            for i in range(len(context_tokens) - len(chunk_tokens) + 1):
                if " ".join(context_tokens[i:i+len(chunk_tokens)]) == chunk_str:
                    chunk_start = i
                    break
            
            context_start = max(0, chunk_start - config.overlap_tokens)
            context_end = min(len(context_tokens), chunk_start + len(chunk_tokens) + config.overlap_tokens)
            context_str = " ".join(context_tokens[context_start:context_end])
            
            # Classify each chunk with its context
            classification = classify_chunk(chunk_str, context_str, config)
            chunks.append({
                "text": chunk_str,
                "classification": classification
            })
            
            # Start a new chunk with overlap
            overlap_tokens = min(config.overlap_tokens, len(current_chunk))
            current_chunk = current_chunk[-overlap_tokens:] if overlap_tokens > 0 else []
            current_token_count = len(" ".join(current_chunk).split())
        
        # Add the sentence to the current chunk
        current_chunk.append(sentence)
        current_token_count += sentence_tokens
    
    # Don't forget the last chunk
    if current_chunk:
        chunk_str = " ".join(current_chunk)
        
        # Get surrounding context for the last chunk
        chunk_tokens = chunk_str.split()
        context_tokens = text.split()
        
        # Find position of chunk in the full text
        chunk_start = 0
        for i in range(len(context_tokens) - len(chunk_tokens) + 1):
            if " ".join(context_tokens[i:i+len(chunk_tokens)]) == chunk_str:
                chunk_start = i
                break
        
        context_start = max(0, chunk_start - config.overlap_tokens)
        context_end = min(len(context_tokens), chunk_start + len(chunk_tokens) + config.overlap_tokens)
        context_str = " ".join(context_tokens[context_start:context_end])
        
        # Classify the last chunk
        classification = classify_chunk(chunk_str, context_str, config)
        chunks.append({
            "text": chunk_str,
            "classification": classification
        })
    
    return chunks 