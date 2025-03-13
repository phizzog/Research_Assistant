import json
import re
import logging
import os
from typing import List, Dict, Any
import tiktoken
from pathlib import Path

# Configure logging for transparency and debugging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# Constants
MAX_TOKENS_PER_CHUNK = 700  # Target chunk size in tokens

# Regex pattern for identifying section headers typical in research papers
SECTION_PATTERN = re.compile(r'^[A-Z][\w\s\d.,:;!?()\-—–]+$', re.MULTILINE)

# Token counting setup with tiktoken
ENCODING = tiktoken.get_encoding("cl100k_base")  # Compatible with modern models

class PDFChunker:
    """Class for chunking PDF content into manageable pieces for embedding"""
    
    def __init__(self, input_file: str = None, output_file: str = None):
        """Initialize the PDF chunker with input and output file paths"""
        self.input_file = input_file
        self.output_file = output_file
        
    def load_json(self, file_path: str = None) -> Dict[str, Any]:
        """Load JSON data from a file."""
        file_path = file_path or self.input_file
        logger.info(f"Loading JSON from {file_path}")
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data
    
    def save_chunks(self, chunks: List[Dict[str, Any]], output_file: str = None):
        """Save the chunked data to a JSON file."""
        output_file = output_file or self.output_file
        logger.info(f"Saving chunked data to {output_file}")
        
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        
        output_data = {
            "chunks": chunks
        }
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2)
        logger.info(f"Saved {len(chunks)} chunks to {output_file}")
    
    def concatenate_page_texts(self, pages: List[Dict[str, Any]]) -> (str, List[Dict[str, Any]]):
        """Concatenate page texts into a single string and track page indices."""
        logger.info("Concatenating page texts and tracking indices")
        full_text = ""
        page_indices = []
        current_index = 0

        for page in pages:
            page_text = page['text'] + "\n\n"
            start_index = current_index
            end_index = start_index + len(page_text)
            page_indices.append({
                "page_id": page['page_id'],
                "start_index": start_index,
                "end_index": end_index
            })
            full_text += page_text
            current_index = end_index

        return full_text, page_indices
    
    def identify_boundaries_and_paragraphs(self, full_text: str) -> List[Dict[str, Any]]:
        """Identify structural boundaries and split into paragraphs with index tracking."""
        logger.info("Identifying boundaries and splitting into paragraphs")
        chunks = []
        current_section = None
        current_text = ""
        current_start_index = 0

        lines = full_text.splitlines(True)  # Preserve newlines
        for line in lines:
            line_stripped = line.strip()

            # Check for section headers
            section_match = SECTION_PATTERN.match(line_stripped)
            if section_match and len(line_stripped) > 5:  # Minimum length to avoid false positives
                if current_text:
                    chunks.extend(self.split_into_paragraph_chunks(current_text, current_section, current_start_index))
                current_section = line_stripped
                current_text = ""
                current_start_index += len(line)
                continue

            # Accumulate text under the current section
            current_text += line

        # Add the final chunk
        if current_text:
            chunks.extend(self.split_into_paragraph_chunks(current_text, current_section, current_start_index))

        return chunks
    
    def split_into_paragraph_chunks(self, text: str, section: str, start_index: int) -> List[Dict[str, Any]]:
        """Split text into paragraph-based chunks within token limits."""
        logger.info(f"Splitting text into paragraph chunks for section: {section or 'No Section'}")
        paragraphs = re.split(r'\n\n+', text)
        chunks = []
        current_index = start_index

        for paragraph in paragraphs:
            paragraph = paragraph.strip()
            if not paragraph:
                continue

            paragraph_start = current_index
            paragraph_end = paragraph_start + len(paragraph)
            tokens = ENCODING.encode(paragraph)

            if len(tokens) <= MAX_TOKENS_PER_CHUNK:
                chunks.append({
                    "text": paragraph,
                    "metadata": {
                        "section": section,
                        "start_index": paragraph_start,
                        "end_index": paragraph_end,
                        "sub_chunk": None
                    }
                })
                current_index = paragraph_end
            else:
                # Split large paragraphs by sentence boundaries
                sentences = re.split(r'(?<=[.!?])\s+', paragraph)
                sub_chunk_text = ""
                sub_chunk_tokens = 0
                sub_chunk_count = 1
                sub_start_index = paragraph_start

                for sentence in sentences:
                    sentence_tokens = ENCODING.encode(sentence)
                    if sub_chunk_tokens + len(sentence_tokens) <= MAX_TOKENS_PER_CHUNK:
                        sub_chunk_text += sentence + " "
                        sub_chunk_tokens += len(sentence_tokens)
                    else:
                        if sub_chunk_text.strip():
                            sub_end_index = sub_start_index + len(sub_chunk_text.strip())
                            chunks.append({
                                "text": sub_chunk_text.strip(),
                                "metadata": {
                                    "section": section,
                                    "start_index": sub_start_index,
                                    "end_index": sub_end_index,
                                    "sub_chunk": f"Part {sub_chunk_count}"
                                }
                            })
                            current_index = sub_end_index
                        sub_chunk_text = sentence + " "
                        sub_chunk_tokens = len(sentence_tokens)
                        sub_start_index = current_index
                        sub_chunk_count += 1

                # Add the final sub-chunk
                if sub_chunk_text.strip():
                    sub_end_index = sub_start_index + len(sub_chunk_text.strip())
                    chunks.append({
                        "text": sub_chunk_text.strip(),
                        "metadata": {
                            "section": section,
                            "start_index": sub_start_index,
                            "end_index": sub_end_index,
                            "sub_chunk": f"Part {sub_chunk_count}" if sub_chunk_count > 1 else None
                        }
                    })
                    current_index = sub_end_index

        return chunks
    
    def process_tables(self, pages: List[Dict[str, Any]], chunks: List[Dict[str, Any]], page_indices: List[Dict[str, Any]]):
        """Append table content to chunks based on index overlaps."""
        logger.info("Processing tables and appending to relevant chunks")
        for page in pages:
            page_id = page['page_id']
            page_index = next((p for p in page_indices if p['page_id'] == page_id), None)
            if not page_index or not page.get('tables'):
                continue

            page_start = page_index['start_index']
            page_end = page_index['end_index']

            for table in page['tables']:
                table_text = f"Table {table['table_id']}:\n"
                for row in table['data']:
                    table_text += " | ".join(row) + "\n"
                table_text = table_text.strip()

                # Append table to overlapping chunks
                for chunk in chunks:
                    chunk_start = chunk['metadata']['start_index']
                    chunk_end = chunk['metadata']['end_index']
                    if chunk_start < page_end and chunk_end > page_start:
                        chunk['text'] += "\n" + table_text

        return chunks
    
    def get_overlapping_pages(self, chunk: Dict[str, Any], page_indices: List[Dict[str, Any]]) -> List[str]:
        """Determine which pages a chunk overlaps with."""
        chunk_start = chunk['metadata']['start_index']
        chunk_end = chunk['metadata']['end_index']
        overlapping_pages = [
            p['page_id'] for p in page_indices
            if p['start_index'] < chunk_end and p['end_index'] > chunk_start
        ]
        return overlapping_pages
    
    def add_page_ids(self, chunks: List[Dict[str, Any]], page_indices: List[Dict[str, Any]]):
        """Add page IDs to chunk metadata for image linking."""
        logger.info("Adding page IDs to chunks for image association")
        for chunk in chunks:
            chunk['metadata']['page_ids'] = self.get_overlapping_pages(chunk, page_indices)
    
    def process(self, input_file: str = None, output_file: str = None) -> List[Dict[str, Any]]:
        """Process the JSON file and chunk the data."""
        try:
            # Set file paths if provided
            if input_file:
                self.input_file = input_file
            if output_file:
                self.output_file = output_file
                
            # Ensure input file is set
            if not self.input_file:
                raise ValueError("Input file path is required")
                
            # Load JSON
            data = self.load_json()
            pages = data['pages']  # Assuming parser output has a 'pages' key

            # Concatenate page texts and track indices
            full_text, page_indices = self.concatenate_page_texts(pages)

            # Identify boundaries and split into chunks
            chunks = self.identify_boundaries_and_paragraphs(full_text)

            # Process tables
            chunks = self.process_tables(pages, chunks, page_indices)

            # Add page IDs for image linking
            self.add_page_ids(chunks, page_indices)

            # Save chunks if output file is specified
            if self.output_file:
                self.save_chunks(chunks)

            return chunks

        except Exception as e:
            logger.error(f"Error processing JSON: {str(e)}", exc_info=True)
            raise

def main():
    """Main function to process the JSON file and chunk the data."""
    # Define paths
    script_dir = os.path.dirname(os.path.abspath(__file__))
    input_file = os.path.join(script_dir, "..", "..", "input", "parsed_pdf.json")
    output_file = os.path.join(script_dir, "..", "..", "output", "chunked_research.json")
    
    # Create directories if they don't exist
    os.makedirs(os.path.dirname(input_file), exist_ok=True)
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    # Process the PDF
    chunker = PDFChunker(input_file, output_file)
    chunker.process()

if __name__ == "__main__":
    main() 