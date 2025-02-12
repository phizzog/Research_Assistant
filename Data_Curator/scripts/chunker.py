from typing import List, Dict, Union, Any
from .config import ChunkingConfig, CLASSIFY_PROMPT_PATH
import json
import requests
from .definitions import DEFINITIONS

def classify_chunk(text: str, context: str, config: ChunkingConfig) -> str:
    """
    Classifies a chunk of text using the Ollama model and research definitions.
    Returns one of: 'qualitative', 'quantitative', 'mixed', or 'general'.
    
    Args:
        text: The text chunk to classify
        context: Surrounding context from adjacent chunks/pages
        config: Configuration settings
    """
    # Construct the prompt directly in the code
    prompt = f"""You are tasked with classifying a given text as either 'qualitative', 'quantitative', 'mixed', or 'general' research. To help you make this classification, please use the following definitions:

Qualitative Research:
<qualitative_def>
{DEFINITIONS['qualitative']}
</qualitative_def>

Quantitative Research:
<quantitative_def>
{DEFINITIONS['quantitative']}
</quantitative_def>

Mixed Methods:
<mixed_def>
{DEFINITIONS['mixed']}
</mixed_def>

Now, carefully read and analyze the following text and its surrounding context:

<context>
{context}
</context>

<text_to_classify>
{text}
</text_to_classify>

Based on the definitions provided and your analysis of both the text and its context, determine which category it best fits into. Consider the following:

1. Does the text primarily discuss non-numerical data, experiences, or interpretations?
2. Does it focus on numerical data, statistical analysis, or measurable variables?
3. Does it combine both qualitative and quantitative elements?
4. If it doesn't clearly fit into any of these categories, it may be classified as 'general'.

Provide your reasoning for the classification in <reasoning> tags. Your reasoning should be concise but clear, explaining why you believe the text fits best into the chosen category.

After providing your reasoning, give your final classification as a single word response. Use ONLY ONE of these exact words: qualitative, quantitative, mixed, or general.

Your complete response should be structured as follows:

<reasoning>
[Your reasoning here]
</reasoning>

<classification>
[Your one-word classification here]
</classification>"""

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
        response_text = response.json().get('response', '').strip().lower()
        
        # Extract classification from the response
        if '<classification>' in response_text:
            classification = response_text.split('<classification>')[-1].split('</classification>')[0].strip()
        else:
            classification = response_text.strip()
        
        # Validate the response is one of our expected classifications
        valid_classifications = {'qualitative', 'quantitative', 'mixed', 'general'}
        if classification in valid_classifications:
            return classification
        return 'general'  # Default if response is not valid
        
    except Exception as e:
        print(f"Error classifying chunk: {e}")
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
            # Get surrounding context
            context_start = max(0, start - config.overlap_tokens)
            context_end = min(len(tokens), end + config.overlap_tokens)
            context_str = " ".join(tokens[context_start:context_end])
            
            # Classify each chunk with its context
            classification = classify_chunk(chunk_str, context_str, config)
            chunks.append({
                "text": chunk_str,
                "classification": classification
            })
        # Move start to create overlap
        start = max(end - config.overlap_tokens, end)

    return chunks 