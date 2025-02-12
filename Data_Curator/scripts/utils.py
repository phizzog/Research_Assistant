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
                f"{OLLAMA_BASE_URL}/api/generate",
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

        except Exception as e:
            end_time = time.time()
            duration = end_time - start_time
            perf_logger.error(f"Request failed in {duration:.2f}s on attempt {attempt + 1}: {str(e)}")
            if attempt == config.max_retries - 1:
                logger.error("All retries failed", exc_info=True)
                return ""

    return "" 