import re
import time
import logging
import requests
from typing import Optional
from .config import ChunkingConfig, OLLAMA_BASE_URL

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

def get_raw_response(prompt: str, config: ChunkingConfig) -> str:
    """
    Sends a prompt to Ollama using its native API and returns the complete text response.
    Includes improved error handling with fallback responses.
    """
    logger = logging.getLogger(__name__)
    perf_logger = logging.getLogger('performance')
    
    logger.debug("=" * 80)
    logger.debug("SENDING PROMPT TO OLLAMA (raw):")
    logger.debug(f"Prompt:\n{prompt}")

    start_time = time.time()

    payload = {
        "model": config.model,
        "prompt": prompt,
        "stream": False
    }

    for attempt in range(config.max_retries):
        try:
            if attempt > 0:
                time.sleep(config.cooldown)
                perf_logger.info(f"Retry attempt {attempt + 1} after {config.cooldown:.2f}s cooldown")

            response = requests.post(
                f"{config.ollama_base_url}/api/generate",
                json=payload,
                timeout=30
            )
            
            response.raise_for_status()
            response_data = response.json()
            
            response_text = response_data.get('response', '')
            
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

        except requests.exceptions.RequestException as e:
            end_time = time.time()
            duration = end_time - start_time
            perf_logger.error(f"Request failed in {duration:.2f}s on attempt {attempt + 1}: {str(e)}")
            
            # Continue to next retry attempt if not the last one
            if attempt < config.max_retries - 1:
                continue
                
            # On final attempt, create a fallback response based on the prompt type
            logger.error("All retries failed, generating fallback response", exc_info=True)
            
            # Determine the type of prompt and create appropriate fallback
            if "<chunk_id>" in prompt:
                # This is a chunk prompt
                chunk_id = extract_tag(prompt, "chunk_id")
                raw_text = extract_tag(prompt, "raw_text")
                return f"<chunk_id>{chunk_id}</chunk_id>\n<raw_text>{raw_text}</raw_text>\n<contextualized_chunk>{raw_text}</contextualized_chunk>"
            
            elif "<table_id>" in prompt:
                # This is a table prompt
                table_id = extract_tag(prompt, "table_id")
                raw_table = extract_tag(prompt, "raw_table")
                return f"<table_id>{table_id}</table_id>\n<raw_table>{raw_table}</raw_table>\n<contextualized_table>Unable to contextualize table due to service error.</contextualized_table>"
            
            elif "<text_to_classify>" in prompt:
                # This is a classification prompt
                return "<classification>general</classification>"
            
            else:
                # Generic fallback
                return "Error: Unable to generate response after multiple attempts."
        
        except Exception as e:
            end_time = time.time()
            duration = end_time - start_time
            logger.error(f"Unexpected error in {duration:.2f}s: {str(e)}", exc_info=True)
            
            if attempt == config.max_retries - 1:
                # Generic fallback on final attempt
                return "Error: Unexpected error occurred during processing."

    # This should never be reached due to the return statements above
    return "Error: Failed to generate response." 