import json
import requests
import logging
import time
import datetime
import os
import asyncio
import aiohttp
from typing import Dict, List, Optional
from openai import AsyncOpenAI
from dotenv import load_dotenv
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
from pathlib import Path
import yaml
from itertools import cycle

# Load environment variables
load_dotenv()

# Load configuration from YAML file
CONFIG_FILE = "config.yaml"
with open(CONFIG_FILE, "r") as f:
    config = yaml.safe_load(f)

# Configure structured logging
current_time = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
log_dir = Path("logs")
log_dir.mkdir(exist_ok=True)

log_filename = log_dir / f"contextualize_rag_{current_time}.log"
perf_log_filename = log_dir / f"performance_{current_time}.log"

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.FileHandler(log_filename), logging.StreamHandler()]
)

perf_logger = logging.getLogger('performance')
perf_handler = logging.FileHandler(perf_log_filename)
perf_handler.setFormatter(logging.Formatter('%(asctime)s - %(message)s'))
perf_logger.addHandler(perf_handler)
perf_logger.setLevel(logging.INFO)

logger = logging.getLogger(__name__)
logger.info(f"Starting RAG processing run with dual GPUs. Logs at {log_filename}")

# Configuration from YAML
OLLAMA_ENDPOINTS = config["ollama"]["endpoints"]
OLLAMA_MODEL = config["ollama"]["model"]
MAX_RETRIES = config["retries"]["max_retries"]
COOLDOWN = config["retries"]["cooldown"]
BATCH_SIZE = config["processing"]["batch_size"]
EMBEDDING_MODEL = config["embedding"]["model"]

# Embedding model for vectorized retrieval
embedder = SentenceTransformer(EMBEDDING_MODEL, trust_remote_code=True)
logger.info(f"Initialized embedding model: {EMBEDDING_MODEL}")

class RAGContextualizer:
    def __init__(self, document: Dict):
        self.document = document["chunks"]
        self.index = None
        self.embeddings = None
        self.endpoints = cycle(OLLAMA_ENDPOINTS)
        self._build_vector_index()

    def _build_vector_index(self):
        logger.info("Building FAISS index for document chunks")
        start_time = time.time()
        texts = [chunk["text"] for chunk in self.document]
        self.embeddings = embedder.encode(texts, show_progress_bar=True)
        dimension = self.embeddings.shape[1]
        self.index = faiss.IndexFlatL2(dimension)
        self.index.add(self.embeddings)
        duration = time.time() - start_time
        perf_logger.info(f"FAISS index built in {duration:.2f}s with {len(texts)} chunks")
    
    async def _fetch_ollama_response(self, session: aiohttp.ClientSession, prompt: str, endpoint: str) -> str:
        payload = {"model": OLLAMA_MODEL, "prompt": prompt, "stream": False}
        start_time = time.time()
        for attempt in range(MAX_RETRIES):
            try:
                async with session.post(
                    f"{endpoint}/api/generate", json=payload, timeout=30
                ) as response:
                    response.raise_for_status()
                    data = await response.json()
                    text = data.get("response", "").strip()
                    duration = time.time() - start_time
                    perf_logger.info(f"Ollama response from {endpoint} in {duration:.2f}s")
                    logger.debug(f"Raw response from {endpoint} for chunk: {text}")
                    return text
            except Exception as e:
                perf_logger.error(f"Attempt {attempt + 1} failed at {endpoint}: {e}")
                if attempt < MAX_RETRIES - 1:
                    await asyncio.sleep(COOLDOWN)
        logger.error(f"All retries failed for Ollama request at {endpoint}")
        return ""

    def _retrieve_context(self, chunk: Dict, top_k: int = 3) -> str:
        query_embedding = embedder.encode([chunk["text"]])[0]
        distances, indices = self.index.search(np.array([query_embedding]), top_k)
        context_chunks = [
            self.document[idx]["text"] for idx in indices[0] if self.document[idx]["text"] != chunk["text"]
        ]
        context = "\n\n".join(context_chunks)
        logger.debug(f"Retrieved context for chunk, length: {len(context)} chars")
        return context

    async def _contextualize_chunk(self, chunk: Dict, session: aiohttp.ClientSession, endpoint: str) -> Dict:
        chunk_id = f"chunk_{self.document.index(chunk)}"
        raw_text = chunk["text"]
        context = self._retrieve_context(chunk)
        prompt = f"""
        ### Task:
        Enrich the raw text using the provided context for a Retrieval-Augmented Generation (RAG) application. Integrate relevant details, preserve original meaning, and identify the research type (qualitative, quantitative, mixed methods, or general research design principles). Provide only the enriched text with the research type statement as your response, without any additional tags or formatting.

        ### Context:
        {context}

        ### Raw Text:
        {raw_text}
        """
        response = await self._fetch_ollama_response(session, prompt, endpoint)
        
        # Use the response directly as contextualized text
        contextualized_text = response if response else raw_text  # Fallback to raw_text if empty
        if not response:
            logger.warning(f"Empty response for chunk {chunk_id}, using raw text as fallback")

        return {
            "chunk_id": chunk_id,
            "raw_text": raw_text,
            "contextualized_text": contextualized_text,
            "metadata": chunk["metadata"]
        }

    async def process_batch(self, batch: List[Dict]) -> List[Dict]:
        async with aiohttp.ClientSession() as session:
            tasks = []
            for chunk in batch:
                endpoint = next(self.endpoints)
                tasks.append(self._contextualize_chunk(chunk, session, endpoint))
            return await asyncio.gather(*tasks)

    async def run(self) -> List[Dict]:
        logger.info(f"Processing {len(self.document)} chunks in batches of {BATCH_SIZE} across {len(OLLAMA_ENDPOINTS)} GPUs")
        enriched_chunks = []
        for i in range(0, len(self.document), BATCH_SIZE):
            batch = self.document[i:i + BATCH_SIZE]
            batch_result = await self.process_batch(batch)
            enriched_chunks.extend(batch_result)
            logger.info(f"Processed batch {i // BATCH_SIZE + 1}/{(len(self.document) + BATCH_SIZE - 1) // BATCH_SIZE}")
        return enriched_chunks

def save_results(enriched_chunks: List[Dict], output_file: str):
    logger.info(f"Saving to {output_file}")
    try:
        with open(output_file, "w") as f:
            json.dump(enriched_chunks, f, indent=2)
        logger.info("Save successful")
    except Exception as e:
        logger.error(f"Save failed: {e}")
        raise

async def main():
    input_file = config["input_file"]
    output_file = config["output_file"]
    logger.info(f"Loading document from {input_file}")
    with open(input_file, "r") as f:
        document = json.load(f)
    contextualizer = RAGContextualizer(document)
    enriched_chunks = await contextualizer.run()
    save_results(enriched_chunks, output_file)
    print(f"Enriched chunks saved to {output_file}")

if __name__ == "__main__":
    asyncio.run(main())