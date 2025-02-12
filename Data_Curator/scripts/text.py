import json
import sys
from pathlib import Path
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_json_file(file_path: str) -> dict:
    """
    Load and parse JSON file.
    
    Args:
        file_path (str): Path to JSON file
        
    Returns:
        dict: Parsed JSON data
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        logger.error(f"JSON file not found: {file_path}")
        sys.exit(1)
    except json.JSONDecodeError:
        logger.error(f"Invalid JSON file: {file_path}")
        sys.exit(1)

def extract_text_range(json_data: dict, start_page: int, end_page: int, output_file: str) -> None:
    """
    Extract text from specified page range in the JSON data and save to file.
    
    Args:
        json_data (dict): Input JSON containing page data
        start_page (int): Starting page number
        end_page (int): Ending page number
        output_file (str): Path to output text file
    """
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            pages_found = 0
            
            for page in json_data.get("pages", []):
                try:
                    page_num = int(page["page_id"].split("_")[1])
                    
                    if start_page <= page_num <= end_page:
                        # Write page text to file
                        f.write(f"--- Page {page_num} ---\n")
                        f.write(page.get("text", ""))
                        f.write("\n\n")
                        pages_found += 1
                        
                except (ValueError, IndexError, KeyError):
                    logger.warning(f"Skipping page with invalid format: {page.get('page_id', 'UNKNOWN')}")
                    continue
            
            logger.info(f"Processed {pages_found} pages in range {start_page}-{end_page}")
            
    except IOError as e:
        logger.error(f"Error writing to output file: {e}")
        sys.exit(1)

def main():
    """Main function to process JSON and extract text."""
    
    # Check command line arguments
    if len(sys.argv) != 2:
        print("Usage: python text.py <path_to_json_file>")
        sys.exit(1)
    
    # Get input file path
    json_file = sys.argv[1]
    output_file = "text.txt"
    
    # Load JSON data
    logger.info(f"Loading JSON file: {json_file}")
    json_data = load_json_file(json_file)
    
    # Extract text from pages 15-260
    logger.info("Extracting text from pages 15-260")
    extract_text_range(json_data, 15, 260, output_file)
    
    logger.info(f"Text successfully extracted to: {output_file}")

if __name__ == "__main__":
    main()
