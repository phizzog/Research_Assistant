from typing import List
from .config import ChunkingConfig

def chunk_text_tokens(text: str, config: ChunkingConfig) -> List[str]:
    """
    Splits the text by whitespace, grouping up to max_tokens tokens,
    then overlaps the last overlap_tokens tokens into the next chunk.
    """
    tokens = text.split()
    chunks = []
    start = 0

    while start < len(tokens):
        end = start + config.max_tokens
        chunk = " ".join(tokens[start:end])
        if chunk:
            chunks.append(chunk)
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