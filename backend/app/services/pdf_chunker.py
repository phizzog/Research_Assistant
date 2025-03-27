import json
import re
import logging
import os
from typing import List, Dict, Any, Union, Literal
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
MAX_TOKENS_PER_CHUNK = 1500  # Increased from 800 to 1500 for larger chunks with more context
CHUNK_OVERLAP_TOKENS = 300  # Increased from 200 to 300 for better context continuity

# Chunking strategies
PARAGRAPH_CHUNKING = "paragraph"
PAGE_CHUNKING = "page"

# Regex pattern for identifying section headers typical in research papers
SECTION_PATTERN = re.compile(r'^[A-Z][\w\s\d.,:;!?()\-—–]+$', re.MULTILINE)

# Token counting setup with tiktoken
ENCODING = tiktoken.get_encoding("cl100k_base")  # Compatible with modern models

class PDFChunker:
    """Class for chunking PDF content into manageable pieces for embedding"""
    
    def __init__(self, 
                input_file: str = None, 
                output_file: str = None,
                chunking_strategy: Literal["paragraph", "page"] = PARAGRAPH_CHUNKING):
        """Initialize the PDF chunker with input and output file paths and chunking strategy
        
        Args:
            input_file: Path to the input JSON file
            output_file: Path to the output JSON file
            chunking_strategy: Strategy for chunking ("paragraph" for traditional paragraph-based
                              chunking or "page" for page-based chunking where each page is a chunk)
        """
        self.input_file = input_file
        self.output_file = output_file
        self.chunking_strategy = chunking_strategy
        
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
        
        # Load the original data to include document and pages information
        input_data = self.load_json()
        
        # Create output data structure compatible with ParserOutput model
        output_data = {
            "document": input_data.get("document", {}),
            "pages": input_data.get("pages", []),
            "chunks": chunks
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2)
        logger.info(f"Saved {len(chunks)} chunks to {output_file}")
    
    def create_page_based_chunks(self, pages: List[Dict[str, Any]], document_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Create page-based chunks where each page becomes a single chunk.
        
        This is a simpler chunking strategy that preserves the integrity of each page.
        
        Args:
            pages: List of pages from the document
            document_data: Metadata about the document
            
        Returns:
            List of chunks where each chunk corresponds to a page
        """
        logger.info("Creating page-based chunks (one chunk per page)")
        chunks = []
        
        # Format document context
        doc_context = ""
        if document_data:
            title = document_data.get('title', '')
            authors = document_data.get('authors', [])
            publication_date = document_data.get('publication_date', '')
            
            if title:
                doc_context += f"TITLE: {title}\n"
            if authors:
                authors_str = ", ".join(authors)
                doc_context += f"AUTHORS: {authors_str}\n"
            if publication_date:
                doc_context += f"DATE: {publication_date}\n"
            
            if doc_context:
                doc_context += "\n"
        
        # Process each page into a chunk
        for page in pages:
            page_id = page['page_id']
            page_text = page['text']
            
            # Try to identify sections in the page text (simplified approach)
            sections = []
            section_name = "Content"
            for line in page_text.split('\n'):
                line_stripped = line.strip()
                if SECTION_PATTERN.match(line_stripped) and len(line_stripped) > 5:
                    section_name = line_stripped
                    sections.append(section_name)
            
            # Format the chunk content
            chunk_text = doc_context
            
            # Add section info if found
            if sections:
                chunk_text += f"PAGE {page_id} SECTIONS: {', '.join(sections)}\n\n"
            else:
                chunk_text += f"PAGE {page_id}\n\n"
            
            # Add the main page content
            chunk_text += page_text
            
            # Process tables for this page
            if page.get('tables'):
                tables_text = "\n\n"
                for table in page['tables']:
                    tables_text += f"TABLE {table['table_id']}:\n"
                    for row in table['data']:
                        tables_text += " | ".join(row) + "\n"
                    tables_text += "\n"
                
                chunk_text += tables_text
            
            # Create the chunk object
            chunk = {
                "text": chunk_text.strip(),
                "metadata": {
                    "page_id": page_id,
                    "page_ids": [page_id],  # For consistency with paragraph chunking
                    "document_title": document_data.get('title', ''),
                    "document_id": document_data.get('document_id', ''),
                    "chunking_strategy": PAGE_CHUNKING
                }
            }
            
            # Add document metadata
            if document_data.get('authors'):
                chunk["metadata"]["document_authors"] = document_data['authors']
            if document_data.get('publication_date'):
                chunk["metadata"]["document_date"] = document_data['publication_date']
            
            # Add the chunk to the list
            chunks.append(chunk)
        
        logger.info(f"Created {len(chunks)} page-based chunks")
        return chunks
    
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
    
    def extract_sections(self, full_text: str) -> List[Dict[str, Any]]:
        """Extract sections from the full text with their positions."""
        logger.info("Extracting sections from the document")
        sections = []
        current_index = 0
        current_section = "Introduction"  # Default section name if none found
        
        lines = full_text.splitlines(True)  # Preserve newlines
        section_start_index = 0
        
        for i, line in enumerate(lines):
            line_stripped = line.strip()
            
            # Check for section headers
            section_match = SECTION_PATTERN.match(line_stripped)
            if section_match and len(line_stripped) > 5:  # Minimum length to avoid false positives
                if i > 0:  # Not the first line
                    # Store the previous section
                    section_text = "".join(lines[section_start_index:i])
                    sections.append({
                        "name": current_section,
                        "text": section_text,
                        "start_index": current_index + sum(len(lines[j]) for j in range(section_start_index)),
                        "end_index": current_index + sum(len(lines[j]) for j in range(section_start_index, i))
                    })
                
                # Start a new section
                current_section = line_stripped
                section_start_index = i
        
        # Add the final section
        if section_start_index < len(lines):
            section_text = "".join(lines[section_start_index:])
            sections.append({
                "name": current_section,
                "text": section_text,
                "start_index": current_index + sum(len(lines[j]) for j in range(section_start_index)),
                "end_index": current_index + sum(len(lines[j]) for j in range(section_start_index, len(lines)))
            })
        
        return sections
    
    def create_contextual_chunks(self, sections: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Create contextual chunks with section information and paragraph context."""
        logger.info("Creating contextual chunks with section information")
        chunks = []
        
        for section in sections:
            section_name = section["name"]
            section_text = section["text"]
            section_start = section["start_index"]
            
            # Split section into paragraphs
            paragraphs = re.split(r'\n\n+', section_text.strip())
            paragraphs = [p for p in paragraphs if p.strip()]
            
            if not paragraphs:
                continue
                
            # Create chunks from paragraphs with sliding window approach
            current_chunk_text = f"SECTION: {section_name}\n\n"
            current_tokens = len(ENCODING.encode(current_chunk_text))
            current_start_index = section_start
            paragraph_indices = []
            
            # Track paragraph positions within section
            current_position = 0
            for p in paragraphs:
                p_start = section_text.find(p, current_position)
                if p_start != -1:
                    p_end = p_start + len(p)
                    paragraph_indices.append({
                        "text": p,
                        "start": section_start + p_start,
                        "end": section_start + p_end
                    })
                    current_position = p_end
            
            # Create overlapping chunks using sliding window
            i = 0
            while i < len(paragraph_indices):
                current_chunk_text = f"SECTION: {section_name}\n\n"
                current_tokens = len(ENCODING.encode(current_chunk_text))
                chunk_start_index = paragraph_indices[i]["start"]
                
                # Add paragraphs until we hit the token limit
                j = i
                while j < len(paragraph_indices) and current_tokens < MAX_TOKENS_PER_CHUNK:
                    paragraph = paragraph_indices[j]["text"]
                    paragraph_tokens = len(ENCODING.encode(paragraph))
                    
                    # If adding this paragraph would exceed the limit, break
                    if current_tokens + paragraph_tokens > MAX_TOKENS_PER_CHUNK and current_tokens > CHUNK_OVERLAP_TOKENS:
                        break
                    
                    current_chunk_text += paragraph + "\n\n"
                    current_tokens += paragraph_tokens
                    chunk_end_index = paragraph_indices[j]["end"]
                    j += 1
                
                # Ensure we've added at least one paragraph
                if j > i:
                    chunks.append({
                        "text": current_chunk_text.strip(),
                        "metadata": {
                            "section": section_name,
                            "start_index": chunk_start_index,
                            "end_index": chunk_end_index,
                            "paragraph_range": f"{i+1}-{j}",
                            "chunking_strategy": PARAGRAPH_CHUNKING
                        }
                    })
                    
                    # Slide the window with overlap
                    overlap_tokens = 0
                    next_i = i + 1
                    while next_i < j and overlap_tokens < CHUNK_OVERLAP_TOKENS:
                        overlap_tokens += len(ENCODING.encode(paragraph_indices[next_i-1]["text"]))
                        if overlap_tokens >= CHUNK_OVERLAP_TOKENS:
                            break
                        next_i += 1
                    
                    i = max(i + 1, next_i - 1)  # Ensure we advance at least one paragraph
                else:
                    # If we couldn't add any paragraphs, force add the current one and move on
                    paragraph = paragraph_indices[i]["text"]
                    current_chunk_text += paragraph + "\n\n"
                    chunk_end_index = paragraph_indices[i]["end"]
                    
                    chunks.append({
                        "text": current_chunk_text.strip(),
                        "metadata": {
                            "section": section_name,
                            "start_index": chunk_start_index,
                            "end_index": chunk_end_index,
                            "paragraph_range": f"{i+1}",
                            "chunking_strategy": PARAGRAPH_CHUNKING
                        }
                    })
                    i += 1
        
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
                table_text = f"TABLE {table['table_id']}:\n"
                for row in table['data']:
                    table_text += " | ".join(row) + "\n"
                table_text = table_text.strip()

                # Append table to overlapping chunks
                for chunk in chunks:
                    chunk_start = chunk['metadata']['start_index']
                    chunk_end = chunk['metadata']['end_index']
                    if chunk_start < page_end and chunk_end > page_start:
                        # Add table with proper formatting and separation
                        if "TABLE" not in chunk['text']:
                            chunk['text'] += f"\n\n{table_text}"
                        else:
                            # Check if this specific table is already included
                            table_id = f"TABLE {table['table_id']}:"
                            if table_id not in chunk['text']:
                                chunk['text'] += f"\n\n{table_text}"

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
    
    def add_document_context(self, chunks: List[Dict[str, Any]], document_data: Dict[str, Any]):
        """Add document context information to each chunk."""
        logger.info("Adding document context to chunks")
        if document_data:
            title = document_data.get('title', '')
            authors = document_data.get('authors', [])
            publication_date = document_data.get('publication_date', '')
            
            # Format document context
            doc_context = ""
            if title:
                doc_context += f"TITLE: {title}\n"
            if authors:
                authors_str = ", ".join(authors)
                doc_context += f"AUTHORS: {authors_str}\n"
            if publication_date:
                doc_context += f"DATE: {publication_date}\n"
            
            # Add document context to each chunk
            if doc_context:
                doc_context += "\n"
                for chunk in chunks:
                    chunk['text'] = doc_context + chunk['text']
                    # Add document info to metadata too
                    chunk['metadata']['document_title'] = title
                    if authors:
                        chunk['metadata']['document_authors'] = authors
                    if publication_date:
                        chunk['metadata']['document_date'] = publication_date
        
        return chunks
    
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
            document_data = data.get('document', {})

            # Choose chunking strategy
            if self.chunking_strategy == PAGE_CHUNKING:
                # Page-based chunking (each page becomes a chunk)
                logger.info("Using page-based chunking strategy")
                chunks = self.create_page_based_chunks(pages, document_data)
            else:
                # Traditional paragraph-based chunking
                logger.info("Using paragraph-based chunking strategy")
                # Concatenate page texts and track indices
                full_text, page_indices = self.concatenate_page_texts(pages)

                # Extract sections from the document
                sections = self.extract_sections(full_text)

                # Create contextual chunks with overlapping sliding window
                chunks = self.create_contextual_chunks(sections)

                # Process tables
                chunks = self.process_tables(pages, chunks, page_indices)

                # Add page IDs for image linking
                self.add_page_ids(chunks, page_indices)
                
                # Add document context information
                chunks = self.add_document_context(chunks, document_data)

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
    
    # Process the PDF with page-based chunking
    chunker = PDFChunker(input_file, output_file, chunking_strategy=PAGE_CHUNKING)
    chunker.process()

if __name__ == "__main__":
    main() 