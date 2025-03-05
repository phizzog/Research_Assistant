import json
import logging
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("add_book_title.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Hardcoded file paths and book title
INPUT_FILE = "enriched_chunks.json"
OUTPUT_FILE = "updated_enriched_chunks.json"
BOOK_TITLE = "Research_Design_Qualitative,_Quantitative,_and_Mixed_Methods_Approaches"

def add_book_title_to_enriched_chunks():
    """
    Reads enriched chunks from INPUT_FILE, adds BOOK_TITLE to each chunk's metadata,
    and saves the updated data to OUTPUT_FILE.
    """
    logger.info(f"Processing enriched chunks file: {INPUT_FILE}")
    logger.info(f"Adding book title: '{BOOK_TITLE}'")
    
    try:
        # Check if input file exists
        if not os.path.exists(INPUT_FILE):
            logger.error(f"Input file not found: {INPUT_FILE}")
            print(f"Error: Input file not found: {INPUT_FILE}")
            return
        
        # Load the input JSON file
        with open(INPUT_FILE, 'r', encoding='utf-8') as f:
            enriched_chunks = json.load(f)
        
        if not isinstance(enriched_chunks, list):
            logger.error("Input file does not contain a list of chunks")
            print("Error: Input file does not contain a list of chunks")
            return
        
        logger.info(f"Found {len(enriched_chunks)} enriched chunks")
        
        # Update each chunk's metadata
        for chunk in enriched_chunks:
            if "metadata" in chunk:
                chunk["metadata"]["book_title"] = BOOK_TITLE
            else:
                chunk["metadata"] = {"book_title": BOOK_TITLE}
        
        # Save the updated data
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            json.dump(enriched_chunks, f, indent=2)
        
        logger.info(f"Updated {len(enriched_chunks)} enriched chunks with book title")
        logger.info(f"Saved to: {OUTPUT_FILE}")
        print(f"Successfully added book title '{BOOK_TITLE}' to all chunks")
        print(f"Updated file saved to: {OUTPUT_FILE}")
        
    except json.JSONDecodeError:
        logger.error(f"Error: {INPUT_FILE} is not a valid JSON file")
        print(f"Error: {INPUT_FILE} is not a valid JSON file")
    except Exception as e:
        logger.error(f"Error processing enriched chunks file: {str(e)}", exc_info=True)
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    add_book_title_to_enriched_chunks()