import json
import re
import logging
from typing import List, Dict, Any
import tiktoken

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# Constants
MAX_TOKENS_PER_CHUNK = 700  # Target chunk size in tokens
INPUT_FILE = r"/Users/ksnyder/Research-Assistant/Data_Curator/input/test.json"
OUTPUT_FILE = r"/Users/ksnyder/Research-Assistant/Data_Curator/output/chunked_test.json"

# Regex patterns for identifying chapter and section headers
CHAPTER_PATTERN = re.compile(r'^CHAPTER \d+ .+$', re.MULTILINE)
SECTION_PATTERN = re.compile(r'^[A-Z\s\d.,:;!?()\-—–]+$', re.MULTILINE)
PART_PATTERN = re.compile(r'^PART [I]+ .+$', re.MULTILINE)

# Token counting setup with tiktoken
ENCODING = tiktoken.get_encoding("cl100k_base")  # Suitable for most modern models


def load_json(file_path: str) -> Dict[str, Any]:
    """Load JSON data from a file."""
    logger.info(f"Loading JSON from {file_path}")
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data


def concatenate_page_texts(pages: List[Dict[str, Any]]) -> str:
    """Concatenate all page texts into a single string."""
    logger.info("Concatenating page texts")
    full_text = ""
    for page in pages:
        full_text += page['text'] + "\n\n"
    return full_text


def identify_boundaries_and_paragraphs(full_text: str) -> List[Dict[str, Any]]:
    """Identify chapter/section boundaries and split into paragraphs."""
    logger.info("Identifying boundaries and splitting into paragraphs")
    chunks = []
    current_part = None
    current_chapter = None
    current_section = None
    current_text = ""

    lines = full_text.split('\n')
    for line in lines:
        line = line.strip()

        # Check for PART headers
        part_match = PART_PATTERN.match(line)
        if part_match:
            if current_text.strip():
                chunks.extend(split_into_paragraph_chunks(current_text, current_part, current_chapter, current_section))
            current_part = line
            current_chapter = None
            current_section = None
            current_text = ""
            continue

        # Check for CHAPTER headers
        chapter_match = CHAPTER_PATTERN.match(line)
        if chapter_match:
            if current_text.strip():
                chunks.extend(split_into_paragraph_chunks(current_text, current_part, current_chapter, current_section))
            current_chapter = line
            current_section = None
            current_text = line + "\n"
            continue

        # Check for SECTION headers
        section_match = SECTION_PATTERN.match(line)
        if section_match and len(line) > 10 and not line.startswith("PART "):
            if current_text.strip():
                chunks.extend(split_into_paragraph_chunks(current_text, current_part, current_chapter, current_section))
            current_section = line
            current_text = line + "\n"
            continue

        # Accumulate text under the current section
        current_text += line + "\n"

    # Add the final chunk
    if current_text.strip():
        chunks.extend(split_into_paragraph_chunks(current_text, current_part, current_chapter, current_section))

    return chunks


def split_into_paragraph_chunks(text: str, part: str, chapter: str, section: str) -> List[Dict[str, Any]]:
    """Split text into paragraph-based chunks and ensure they fit within token limits."""
    logger.info(f"Splitting text into paragraph chunks for section: {section or 'No Section'}")
    paragraphs = re.split(r'\n\n+', text.strip())
    chunks = []

    for i, paragraph in enumerate(paragraphs):
        paragraph = paragraph.strip()
        if not paragraph:
            continue

        tokens = ENCODING.encode(paragraph)
        if len(tokens) <= MAX_TOKENS_PER_CHUNK:
            chunks.append({
                "text": paragraph,
                "metadata": {
                    "part": part,
                    "chapter": chapter,
                    "section": section,
                    "sub_chunk": None
                }
            })
        else:
            # Split large paragraphs by sentence boundaries
            sentences = re.split(r'(?<=[.!?])\s+', paragraph)
            sub_chunk_text = ""
            sub_chunk_tokens = 0
            sub_chunk_count = 1

            for sentence in sentences:
                sentence_tokens = ENCODING.encode(sentence)
                if sub_chunk_tokens + len(sentence_tokens) <= MAX_TOKENS_PER_CHUNK:
                    sub_chunk_text += sentence + " "
                    sub_chunk_tokens += len(sentence_tokens)
                else:
                    if sub_chunk_text.strip():
                        chunks.append({
                            "text": sub_chunk_text.strip(),
                            "metadata": {
                                "part": part,
                                "chapter": chapter,
                                "section": section,
                                "sub_chunk": f"Part {sub_chunk_count}"
                            }
                        })
                    sub_chunk_text = sentence + " "
                    sub_chunk_tokens = len(sentence_tokens)
                    sub_chunk_count += 1

            # Add the final sub-chunk if any text remains
            if sub_chunk_text.strip():
                chunks.append({
                    "text": sub_chunk_text.strip(),
                    "metadata": {
                        "part": part,
                        "chapter": chapter,
                        "section": section,
                        "sub_chunk": f"Part {sub_chunk_count}" if sub_chunk_count > 1 else None
                    }
                })

    return chunks


def process_tables(pages: List[Dict[str, Any]], chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Append table content to the relevant chunk based on page ID."""
    logger.info("Processing tables and appending to relevant chunks")
    page_to_chunk_map = {}
    for chunk in chunks:
        text = chunk['text']
        for page in pages:
            if page['text'] in text:
                page_to_chunk_map[page['page_id']] = chunk
                break

    for page in pages:
        if page.get('tables'):
            chunk = page_to_chunk_map.get(page['page_id'])
            if chunk:
                for table in page['tables']:
                    table_text = f"Table {table['table_id']}:\n"
                    for row in table['data']:
                        table_text += " | ".join(row) + "\n"
                    chunk['text'] += "\n" + table_text.strip()

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
    # Step 1: Load JSON
    data = load_json(INPUT_FILE)
    pages = data['pages']

    # Step 2: Concatenate page texts
    full_text = concatenate_page_texts(pages)

    # Step 3: Identify boundaries and split into paragraph-based chunks
    chunks = identify_boundaries_and_paragraphs(full_text)

    # Step 4: Process tables
    chunks = process_tables(pages, chunks)

    # Step 5: Store chunks
    save_chunks(chunks, OUTPUT_FILE)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.error(f"Error processing JSON: {str(e)}", exc_info=True)