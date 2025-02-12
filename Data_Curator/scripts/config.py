import os
from dataclasses import dataclass
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables
load_dotenv()

# Ollama configuration
OLLAMA_BASE_URL = 'http://192.168.10.3:11436'

@dataclass
class ChunkingConfig:
    context_pages: int = 5
    max_retries: int = 2
    cooldown: float = 0.1
    model: str = "gemma:7b"
    max_tokens: int = 300
    overlap_tokens: int = 50

# Get the absolute path to the project root
PROJECT_ROOT = Path(__file__).parent.parent

# Prompt file paths
PROMPTS_DIR = PROJECT_ROOT / 'prompts'
CHUNK_PROMPT_PATH = str(PROMPTS_DIR / 'chunk_prompt.txt')
TABLE_PROMPT_PATH = str(PROMPTS_DIR / 'table_prompt.txt') 