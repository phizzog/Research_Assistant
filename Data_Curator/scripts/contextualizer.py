import json
import logging
from typing import Dict, List
from .config import ChunkingConfig, CHUNK_PROMPT_PATH, TABLE_PROMPT_PATH
from .utils import get_raw_response, extract_tag

logger = logging.getLogger(__name__)

def load_prompt_template(template_path: str) -> str:
    """Load prompt template from file"""
    with open(template_path, 'r') as f:
        return f.read()

def generate_chunk_context(
    chunk_text: str,
    context: str,
    chunk_id: str,
    config: ChunkingConfig
) -> dict:
    """
    Creates a prompt to enrich the chunk_text with the context.
    Returns a dictionary containing enriched chunk information.
    """
    template = load_prompt_template(CHUNK_PROMPT_PATH)
    prompt = template.format(
        chunk_id=chunk_id,
        chunk_text=chunk_text,
        context=context
    )

    response_text = get_raw_response(prompt, config)

    # Extract the raw text and classification separately
    raw_text = extract_tag(response_text, "raw_text")
    contextualized_chunk = extract_tag(response_text, "contextualized_chunk")
    
    # Extract just the text from the raw_text field if it's in JSON format
    if raw_text.startswith("{'text':"):
        try:
            raw_data = eval(raw_text)
            text = raw_data.get('text', '')
            classification = raw_data.get('classification', 'general')
        except:
            text = raw_text
            classification = 'general'
    else:
        text = raw_text
        classification = 'general'

    return {
        "chunk_id": extract_tag(response_text, "chunk_id"),
        "text": text,
        "classification": classification,
        "contextualized_chunk": contextualized_chunk
    }

def generate_table_context(
    table_data: List[List[str]],
    context: str,
    table_id: str,
    config: ChunkingConfig
) -> dict:
    """
    Creates a prompt to enrich table_data with the context.
    Returns a dictionary containing enriched table information.
    """
    template = load_prompt_template(TABLE_PROMPT_PATH)
    table_json = json.dumps(table_data)
    
    prompt = template.format(
        table_id=table_id,
        table_json=table_json,
        context=context
    )

    response_text = get_raw_response(prompt, config)

    return {
        "table_id": extract_tag(response_text, "table_id"),
        "raw_table": extract_tag(response_text, "raw_table"),
        "contextualized_table": extract_tag(response_text, "contextualized_table")
    } 