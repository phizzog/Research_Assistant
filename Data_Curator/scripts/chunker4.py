import json
import re
import logging
from typing import List, Dict, Any
import tiktoken
import os

# Configure logging for transparency and debugging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# Constants
MAX_TOKENS_PER_CHUNK = 700  # Target chunk size in tokens
# Make paths relative to the script location
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
INPUT_FILE = os.path.join(SCRIPT_DIR, "..", "input", "test.json")
OUTPUT_FILE = os.path.join(SCRIPT_DIR, "..", "output", "chunked_test2.json")

# Regex patterns for identifying structural headers
CHAPTER_PATTERN = re.compile(r'^CHAPTER \d+ .+$', re.MULTILINE)
SECTION_PATTERN = re.compile(r'^[A-Z\s\d.,:;!?()\-—–]+$', re.MULTILINE)
PART_PATTERN = re.compile(r'^PART [I]+ .+$', re.MULTILINE)

# Token counting setup with tiktoken
ENCODING = tiktoken.get_encoding("cl100k_base")  # Compatible with modern models


def load_json(file_path: str) -> Dict[str, Any]:
    """Load JSON data from a file."""
    logger.info(f"Loading JSON from {file_path}")
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data


def concatenate_page_texts(pages: List[Dict[str, Any]]) -> (str, List[Dict[str, Any]]):
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


def identify_boundaries_and_paragraphs(full_text: str) -> List[Dict[str, Any]]:
    """Identify structural boundaries and split into paragraphs with index tracking."""
    logger.info("Identifying boundaries and splitting into paragraphs with index tracking")
    chunks = []
    current_part = None
    current_chapter = None
    current_section = None
    current_text = ""
    current_start_index = 0

    lines = full_text.splitlines(True)  # Preserve newlines
    for line in lines:
        line_stripped = line.strip()

        # Check for PART headers
        part_match = PART_PATTERN.match(line_stripped)
        if part_match:
            if current_text:
                chunks.extend(split_into_paragraph_chunks(current_text, current_part, current_chapter, current_section, current_start_index, full_text))
            current_part = line_stripped
            current_chapter = None
            current_section = None
            current_text = ""
            current_start_index += len(line)
            continue

        # Check for CHAPTER headers
        chapter_match = CHAPTER_PATTERN.match(line_stripped)
        if chapter_match:
            if current_text:
                chunks.extend(split_into_paragraph_chunks(current_text, current_part, current_chapter, current_section, current_start_index, full_text))
            current_chapter = line_stripped
            current_section = None
            current_text = line
            current_start_index += len(line)
            continue

        # Check for SECTION headers
        section_match = SECTION_PATTERN.match(line_stripped)
        if section_match and len(line_stripped) > 10 and not line_stripped.startswith("PART "):
            if current_text:
                chunks.extend(split_into_paragraph_chunks(current_text, current_part, current_chapter, current_section, current_start_index, full_text))
            current_section = line_stripped
            current_text = line
            current_start_index += len(line)
            continue

        # Accumulate text under the current section
        current_text += line

    # Add the final chunk
    if current_text:
        chunks.extend(split_into_paragraph_chunks(current_text, current_part, current_chapter, current_section, current_start_index, full_text))

    return chunks


def split_into_paragraph_chunks(text: str, part: str, chapter: str, section: str, start_index: int, full_text: str) -> List[Dict[str, Any]]:
    """Split text into paragraph-based chunks within token limits, tracking indices."""
    logger.info(f"Splitting text into paragraph chunks for section: {section or 'No Section'}")
    paragraphs = re.split(r'\n\n+', text)
    chunks = []
    current_index = start_index

    for paragraph in paragraphs:
        paragraph = paragraph.strip()
        if not paragraph:
            continue

        paragraph_start = full_text.find(paragraph, current_index)
        paragraph_end = paragraph_start + len(paragraph)

        tokens = ENCODING.encode(paragraph)
        if len(tokens) <= MAX_TOKENS_PER_CHUNK:
            chunks.append({
                "text": paragraph,
                "metadata": {
                    "part": part,
                    "chapter": chapter,
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
                                "part": part,
                                "chapter": chapter,
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
                        "part": part,
                        "chapter": chapter,
                        "section": section,
                        "start_index": sub_start_index,
                        "end_index": sub_end_index,
                        "sub_chunk": f"Part {sub_chunk_count}" if sub_chunk_count > 1 else None
                    }
                })
                current_index = sub_end_index

    return chunks


def process_tables(pages: List[Dict[str, Any]], chunks: List[Dict[str, Any]], page_indices: List[Dict[str, Any]]):
    """Append table content to chunks based on index overlaps."""
    logger.info("Processing tables and appending to relevant chunks based on index overlaps")

    for page in pages:
        page_id = page['page_id']
        page_index = next((p for p in page_indices if p['page_id'] == page_id), None)
        if not page_index:
            continue

        page_start = page_index['start_index']
        page_end = page_index['end_index']

        if page.get('tables'):
            for table in page['tables']:
                table_text = f"Table {table['table_id']}:\n"
                for row in table['data']:
                    table_text += " | ".join(row) + "\n"
                table_text = table_text.strip()

                # Append table to overlapping chunks
                for chunk in chunks:
                    chunk_start = chunk['metadata']['start_index']
                    chunk_end = chunk['metadata']['end_index']
                    if (chunk_start < page_end and chunk_end > page_start):
                        chunk['text'] += "\n" + table_text

    return chunks


def save_chunks(chunks: List[Dict[str, Any]], output_file: str):
    """Save the chunked data to a JSON file."""
    logger.info(f"Saving chunked data to {output_file}")
    output_data = {
        "chunks": chunks
    }
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2)
    logger.info(f"Saved {len(chunks)} chunks to {output_file}")


def main():
    """Main function to process the JSON file and chunk the data."""
    # Load JSON
    data = load_json(INPUT_FILE)
    pages = data['pages']

    # Concatenate page texts and track indices
    full_text, page_indices = concatenate_page_texts(pages)

    # Identify boundaries and split into chunks
    chunks = identify_boundaries_and_paragraphs(full_text)

    # Process tables
    chunks = process_tables(pages, chunks, page_indices)

    # Save chunks
    save_chunks(chunks, OUTPUT_FILE)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.error(f"Error processing JSON: {str(e)}", exc_info=True)