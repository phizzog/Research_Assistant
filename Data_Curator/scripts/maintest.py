import json
import logging
import datetime
import os
from typing import Dict, List
import sys
from pathlib import Path
import requests

# Add the parent directory to sys.path when running directly
if __name__ == "__main__":
    sys.path.append(str(Path(__file__).parent.parent.parent))

from Data_Curator.scripts.config import ChunkingConfig
from Data_Curator.scripts.chunker import chunk_text_tokens, get_page_context, classify_chunk
from Data_Curator.scripts.contextualizer import generate_chunk_context, generate_table_context

def setup_logging() -> None:
    """Configure logging for the application"""
    current_time = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    log_filename = f"logs/contextualize_{current_time}.log"
    model_log_filename = f"logs/model_output_{current_time}.log"
    
    # Ensure logs directory exists
    os.makedirs('logs', exist_ok=True)

    # Main logger configuration with colored output
    main_formatter = logging.Formatter(
        '\n%(asctime)s [%(levelname)s] %(name)s\n'
        '━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n'
        '%(message)s\n'
    )

    # Use UTF-8 encoding for all log files
    file_handler = logging.FileHandler(log_filename, encoding='utf-8')
    file_handler.setFormatter(main_formatter)

    # For console output, handle encoding issues gracefully
    class EncodingStreamHandler(logging.StreamHandler):
        def emit(self, record):
            try:
                msg = self.format(record)
                stream = self.stream
                # Replace problematic characters if needed for console output
                stream.write(msg.encode('utf-8', errors='replace').decode(stream.encoding, errors='replace') + self.terminator)
                self.flush()
            except Exception:
                self.handleError(record)

    console_handler = EncodingStreamHandler()
    console_handler.setFormatter(main_formatter)

    logging.basicConfig(
        level=logging.INFO,
        handlers=[file_handler, console_handler]
    )

    # Performance logger setup with cleaner metrics format
    perf_logger = logging.getLogger('performance')
    perf_formatter = logging.Formatter(
        '\n%(asctime)s [METRICS]\n'
        '┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈┈\n'
        '%(message)s\n'
    )
    
    perf_handler = logging.FileHandler(f"logs/performance_{current_time}.log", encoding='utf-8')
    perf_handler.setFormatter(perf_formatter)
    perf_logger.addHandler(perf_handler)
    perf_logger.setLevel(logging.INFO)

    # Model output logger setup
    model_logger = logging.getLogger('model_output')
    model_formatter = logging.Formatter(
        '\n%(asctime)s [MODEL OUTPUT]\n'
        '════════════════════════════════════════\n'
        '%(message)s\n'
        '════════════════════════════════════════\n'
    )
    
    model_handler = logging.FileHandler(model_log_filename, encoding='utf-8')
    model_handler.setFormatter(model_formatter)
    model_logger.addHandler(model_handler)
    model_logger.setLevel(logging.INFO)

    # Create a logger instance for this module
    logger = logging.getLogger(__name__)
    logger.info("Logging system initialized")
    
    return logger

def check_ollama_connection(config: ChunkingConfig) -> bool:
    """
    Check if the Ollama API is accessible.
    Returns True if the connection is successful, False otherwise.
    """
    logger = logging.getLogger(__name__)
    logger.info(f"Checking connection to Ollama API at {config.ollama_base_url}")
    
    try:
        # Simple health check request
        response = requests.get(
            f"{config.ollama_base_url}/api/tags",
            timeout=5
        )
        response.raise_for_status()
        logger.info("Successfully connected to Ollama API")
        return True
    except Exception as e:
        logger.error(f"Failed to connect to Ollama API: {e}")
        return False

def transform_document(input_path: str, output_path: str, start_page: int = 0, end_page: int = None) -> None:
    """
    Main function to transform a document by chunking and contextualizing its content.
    
    Args:
        input_path (str): Path to input JSON file
        output_path (str): Path to output JSON file
        start_page (int): Starting page number (0-based index)
        end_page (int): Ending page number (0-based index, inclusive). If None, process until the last page.
    """
    logger = setup_logging()
    logger.info(f"Starting document transformation: {input_path}")
    logger.info(f"Processing pages {start_page} to {end_page if end_page is not None else 'end'}")
    
    start_time = datetime.datetime.now()
    perf_logger = logging.getLogger('performance')
    model_logger = logging.getLogger('model_output')
    
    perf_logger.info(
        f"Transform Process Started\n"
        f"├─ Input: {input_path}\n"
        f"├─ Page Range: {start_page} to {end_page if end_page is not None else 'end'}\n"
        f"├─ Time: {start_time}\n"
        f"└─ Status: Initializing..."
    )

    try:
        # Load input JSON
        with open(input_path, 'r', encoding='utf-8') as f:
            original_data = json.load(f)

        # Configuration
        config = ChunkingConfig()
        logger.info(
            f"Configuration:\n"
            f"├─ Model: {config.model}\n"
            f"├─ Max Tokens: {config.max_tokens}\n"
            f"├─ Overlap: {config.overlap_tokens}\n"
            f"└─ Retries: {config.max_retries}"
        )
        
        # Check Ollama connection before proceeding
        if not check_ollama_connection(config):
            logger.error("Cannot proceed without Ollama connection. Please check the Ollama server and try again.")
            return

        document_metadata = original_data.get("document", {})
        pages = original_data.get("pages", [])

        # Validate and adjust page range
        if end_page is None:
            end_page = len(pages) - 1
        end_page = min(end_page, len(pages) - 1)
        start_page = max(0, min(start_page, end_page))

        # Select only the pages in the specified range
        pages = pages[start_page:end_page + 1]

        new_pages = []
        total_chunks_count = 0

        # Process each page
        for i, page in enumerate(pages):
            page_id = page.get("page_id", f"page_{i + start_page}")
            pdf_title = page.get("pdf_title", "")
            current_text = page.get("text", "")

            # Print progress to console
            print(f"\nProcessing page {i + start_page}/{end_page} ({(i/(len(pages)-1)*100):.1f}% complete)")
            
            # Get context from surrounding pages
            context = get_page_context(pages, i)

            # Chunk the current page text
            chunking_start = datetime.datetime.now()
            print(f"  Chunking text... ", end="", flush=True)
            text_chunks = chunk_text_tokens(current_text, config)
            chunking_end = datetime.datetime.now()
            chunking_duration = (chunking_end - chunking_start).total_seconds()
            print(f"done. Created {len(text_chunks)} chunks in {chunking_duration:.2f}s")
            
            perf_logger.info(
                f"Page Processing Metrics\n"
                f"├─ Page: {i + start_page}/{end_page}\n"
                f"├─ Chunks Generated: {len(text_chunks)}\n"
                f"├─ Chunking Duration: {chunking_duration:.2f}s\n"
                f"└─ Status: Processing chunks..."
            )

            # Process chunks
            new_chunks = []
            for idx, chunk in enumerate(text_chunks, start=1):
                chunk_id = f"{page_id}_chunk_{idx}"
                print(f"  Processing chunk {idx}/{len(text_chunks)} - {chunk.get('classification', 'general')}", end="", flush=True)
                
                logger.info(
                    f"Processing Chunk {idx}/{len(text_chunks)}\n"
                    f"├─ Page: {page_id}\n"
                    f"├─ Classification: {chunk.get('classification', 'general')}\n"
                    f"└─ ID: {chunk_id}"
                )

                chunk_process_start = datetime.datetime.now()
                enriched_chunk = generate_chunk_context(chunk, context, chunk_id, config)
                chunk_process_end = datetime.datetime.now()
                chunk_duration = (chunk_process_end - chunk_process_start).total_seconds()
                print(f" - done in {chunk_duration:.2f}s")

                # Log the model's output
                model_logger.info(
                    f"Chunk Context Generation\n"
                    f"├─ Page: {page_id}\n"
                    f"├─ Chunk: {idx}/{len(text_chunks)}\n"
                    f"├─ Classification: {chunk.get('classification', 'general')}\n"
                    f"├─ Input Text:\n{chunk.get('text', '')}\n"
                    f"├─ Generated Context:\n{enriched_chunk.get('contextualized_chunk', '')}\n"
                    f"└─ Raw Response:\n{enriched_chunk.get('raw_text', '')}"
                )

                perf_logger.info(
                    f"Chunk Processing Metrics\n"
                    f"├─ Chunk: {idx}/{len(text_chunks)}\n"
                    f"├─ Page: {page_id}\n"
                    f"├─ Duration: {chunk_duration:.2f}s\n"
                    f"└─ Status: Complete"
                )

                new_chunks.append(enriched_chunk)

            total_chunks_count += len(new_chunks)

            # Process tables
            new_tables = []
            for t_i, table in enumerate(page.get("tables", []), start=1):
                table_id = table.get("table_id", f"{page_id}_table_{t_i}")
                table_data = table.get("data", [])

                print(f"  Processing table {t_i}/{len(page.get('tables', []))}", end="", flush=True)
                
                logger.info(
                    f"Processing Table {t_i}\n"
                    f"├─ Page: {page_id}\n"
                    f"└─ ID: {table_id}"
                )
                
                table_process_start = datetime.datetime.now()
                enriched_table = generate_table_context(table_data, context, table_id, config)
                table_process_end = datetime.datetime.now()
                table_duration = (table_process_end - table_process_start).total_seconds()
                print(f" - done in {table_duration:.2f}s")

                # Log the model's output for tables
                model_logger.info(
                    f"Table Context Generation\n"
                    f"├─ Page: {page_id}\n"
                    f"├─ Table: {t_i}\n"
                    f"├─ Input Data:\n{json.dumps(table_data, indent=2)}\n"
                    f"├─ Generated Context:\n{enriched_table.get('contextualized_table', '')}\n"
                    f"└─ Raw Response:\n{enriched_table.get('raw_table', '')}"
                )

                table_duration = (table_process_end - table_process_start).total_seconds()
                perf_logger.info(
                    f"Table Processing Metrics\n"
                    f"├─ Table: {t_i}\n"
                    f"├─ Page: {page_id}\n"
                    f"├─ Duration: {table_duration:.2f}s\n"
                    f"└─ Status: Complete"
                )

                new_tables.append(enriched_table)

            # Construct new page
            new_page = {
                "page_id": page_id,
                "pdf_title": pdf_title,
                "text": current_text,
                "text_chunks": new_chunks,
                "tables": new_tables
            }
            new_pages.append(new_page)

        # Prepare final output
        output_data = {
            "document": document_metadata,
            "pages": new_pages,
            "contextual_relationships": {}
        }

        # Create output directory if it doesn't exist
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        # Write output JSON
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)

        end_time = datetime.datetime.now()
        total_duration = (end_time - start_time).total_seconds()
        
        logger.info(
            f"Transformation Summary\n"
            f"├─ Pages Processed: {len(new_pages)}\n"
            f"├─ Total Chunks: {total_chunks_count}\n"
            f"├─ Duration: {total_duration:.2f}s\n"
            f"└─ Status: Complete"
        )
        
        perf_logger.info(
            f"Final Performance Metrics\n"
            f"├─ Total Duration: {total_duration:.2f}s\n"
            f"├─ Pages/Second: {len(new_pages)/total_duration:.2f}\n"
            f"├─ Chunks/Second: {total_chunks_count/total_duration:.2f}\n"
            f"└─ Status: Success"
        )

    except Exception as e:
        logger.error(
            f"Transformation Failed\n"
            f"├─ Error: {str(e)}\n"
            f"└─ Status: Failed",
            exc_info=True
        )
        raise

if __name__ == "__main__":
    try:
        # Get the absolute path to input and output
        script_dir = Path(__file__).parent.parent
        input_path = str(script_dir / "input" / "test.json")
        output_path = str(script_dir / "output" / "contextualized_output.json")
        
        # Check if input file exists
        if not os.path.exists(input_path):
            print(f"Error: Input file not found at {input_path}")
            print("Please ensure the file exists and try again.")
            sys.exit(1)
            
        # Define the page range you want to process (0-based indexing)
        start_page = 253  # Start from the first page
        end_page = 258    # Process up to and including page 2
        
        # Check for fallback mode argument
        fallback_mode = "--fallback" in sys.argv
        if fallback_mode:
            print("Running in fallback mode - will skip Ollama API calls")
            # Monkey patch the functions that call Ollama to return default values
            from Data_Curator.scripts.chunker import classify_chunk
            from Data_Curator.scripts.contextualizer import generate_chunk_context, generate_table_context
            
            # Store original functions
            original_classify = classify_chunk
            original_generate_chunk = generate_chunk_context
            original_generate_table = generate_table_context
            
            # Replace with fallback versions
            def fallback_classify(*args, **kwargs):
                print("  [FALLBACK] Skipping classification API call")
                return "general"
                
            def fallback_generate_chunk(chunk_data, context, chunk_id, config):
                print("  [FALLBACK] Skipping contextualization API call")
                return {
                    "chunk_id": chunk_id,
                    "text": chunk_data.get("text", ""),
                    "classification": chunk_data.get("classification", "general"),
                    "contextualized_chunk": chunk_data.get("text", "")
                }
                
            def fallback_generate_table(table_data, context, table_id, config):
                print("  [FALLBACK] Skipping table contextualization API call")
                return {
                    "table_id": table_id,
                    "raw_table": json.dumps(table_data),
                    "contextualized_table": f"Table with {len(table_data)} rows"
                }
            
            # Apply monkey patches
            import Data_Curator.scripts.chunker
            import Data_Curator.scripts.contextualizer
            Data_Curator.scripts.chunker.classify_chunk = fallback_classify
            Data_Curator.scripts.contextualizer.generate_chunk_context = fallback_generate_chunk
            Data_Curator.scripts.contextualizer.generate_table_context = fallback_generate_table
        
        transform_document(input_path, output_path, start_page, end_page)
    except Exception as e:
        logging.error(f"Failed to process document: {str(e)}", exc_info=True) 