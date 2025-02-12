import json
import logging
import datetime
import os
from typing import Dict, List
import sys
from pathlib import Path

# Add the parent directory to sys.path when running directly
if __name__ == "__main__":
    sys.path.append(str(Path(__file__).parent.parent.parent))

from Data_Curator.scripts.config import ChunkingConfig
from Data_Curator.scripts.chunker import chunk_text_tokens, get_page_context
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

    file_handler = logging.FileHandler(log_filename)
    file_handler.setFormatter(main_formatter)

    console_handler = logging.StreamHandler()
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
    
    perf_handler = logging.FileHandler(f"logs/performance_{current_time}.log")
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
    
    model_handler = logging.FileHandler(model_log_filename)
    model_handler.setFormatter(model_formatter)
    model_logger.addHandler(model_handler)
    model_logger.setLevel(logging.INFO)

    # Create a logger instance for this module
    logger = logging.getLogger(__name__)
    logger.info("Logging system initialized")
    
    return logger

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
        with open(input_path, 'r') as f:
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

            # Get context from surrounding pages
            context = get_page_context(pages, i)

            # Chunk the current page text
            chunking_start = datetime.datetime.now()
            text_chunks = chunk_text_tokens(current_text, config)
            chunking_end = datetime.datetime.now()
            chunking_duration = (chunking_end - chunking_start).total_seconds()
            
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
                logger.info(
                    f"Processing Chunk {idx}/{len(text_chunks)}\n"
                    f"├─ Page: {page_id}\n"
                    f"└─ ID: {chunk_id}"
                )

                chunk_process_start = datetime.datetime.now()
                enriched_chunk = generate_chunk_context(chunk, context, chunk_id, config)
                chunk_process_end = datetime.datetime.now()

                # Log the model's output
                model_logger.info(
                    f"Chunk Context Generation\n"
                    f"├─ Page: {page_id}\n"
                    f"├─ Chunk: {idx}/{len(text_chunks)}\n"
                    f"├─ Input Text:\n{chunk}\n"
                    f"├─ Generated Context:\n{enriched_chunk.get('contextualized_chunk', '')}\n"
                    f"└─ Raw Response:\n{enriched_chunk.get('raw_text', '')}"
                )

                chunk_duration = (chunk_process_end - chunk_process_start).total_seconds()
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

                logger.info(
                    f"Processing Table {t_i}\n"
                    f"├─ Page: {page_id}\n"
                    f"└─ ID: {table_id}"
                )
                
                table_process_start = datetime.datetime.now()
                enriched_table = generate_table_context(table_data, context, table_id, config)
                table_process_end = datetime.datetime.now()

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
        with open(output_path, 'w') as f:
            json.dump(output_data, f, indent=2)

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
        
        # Define the page range you want to process (0-based indexing)
        start_page = 253  # Start from the first page
        end_page = 258    # Process up to and including page 2
        
        transform_document(input_path, output_path, start_page, end_page)
    except Exception as e:
        logging.error(f"Failed to process document: {str(e)}") 