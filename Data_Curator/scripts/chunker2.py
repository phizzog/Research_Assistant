import json
import re
import logging
from typing import List, Dict, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# Constants
MAX_WORDS_PER_CHUNK = 1000  # Maximum words per chunk before splitting
INPUT_FILE = r"C:\Users\kenny\OneDrive\code\Research-Assistant\Data_Curator\input\test.json"    # Replace with your input JSON file path
OUTPUT_FILE = r"C:\Users\kenny\OneDrive\code\Research-Assistant\Data_Curator\output\chunked_examplename.json"

# Regex patterns for identifying chapter and section headers
CHAPTER_PATTERN = re.compile(r'^CHAPTER \d+ .+$', re.MULTILINE)
SECTION_PATTERN = re.compile(r'^[A-Z\s\d.,:;!?()\-—–]+$', re.MULTILINE)
PART_PATTERN = re.compile(r'^PART [I]+ .+$', re.MULTILINE)


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


def identify_boundaries(full_text: str) -> List[Dict[str, str]]:
    """Identify chapter and section boundaries and split text into chunks."""
    logger.info("Identifying chapter and section boundaries")
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
                chunks.append({
                    "text": current_text.strip(),
                    "metadata": {
                        "part": current_part,
                        "chapter": current_chapter,
                        "section": current_section
                    }
                })
            current_part = line
            current_chapter = None
            current_section = None
            current_text = ""
            continue

        # Check for CHAPTER headers
        chapter_match = CHAPTER_PATTERN.match(line)
        if chapter_match:
            if current_text.strip():
                chunks.append({
                    "text": current_text.strip(),
                    "metadata": {
                        "part": current_part,
                        "chapter": current_chapter,
                        "section": current_section
                    }
                })
            current_chapter = line
            current_section = None
            current_text = line + "\n"
            continue

        # Check for SECTION headers
        section_match = SECTION_PATTERN.match(line)
        if section_match and len(line) > 10 and not line.startswith("PART "):  # Avoid short uppercase lines
            if current_text.strip():
                chunks.append({
                    "text": current_text.strip(),
                    "metadata": {
                        "part": current_part,
                        "chapter": current_chapter,
                        "section": current_section
                    }
                })
            current_section = line
            current_text = line + "\n"
            continue

        # Accumulate text under the current section
        current_text += line + "\n"

    # Add the final chunk
    if current_text.strip():
        chunks.append({
            "text": current_text.strip(),
            "metadata": {
                "part": current_part,
                "chapter": current_chapter,
                "section": current_section
            }
        })

    return chunks


def split_large_chunks(chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Split chunks exceeding the word limit into smaller sub-chunks."""
    logger.info(f"Splitting chunks exceeding {MAX_WORDS_PER_CHUNK} words")
    new_chunks = []
    for chunk in chunks:
        text = chunk['text']
        metadata = chunk['metadata']
        words = text.split()

        if len(words) <= MAX_WORDS_PER_CHUNK:
            new_chunks.append(chunk)
        else:
            logger.info(f"Splitting large chunk: {metadata['section'] or 'No Section'} with {len(words)} words")
            sub_chunks = []
            current_sub_chunk = []
            word_count = 0

            for word in words:
                if word_count + 1 > MAX_WORDS_PER_CHUNK and current_sub_chunk:
                    sub_chunks.append(" ".join(current_sub_chunk))
                    current_sub_chunk = []
                    word_count = 0
                current_sub_chunk.append(word)
                word_count += 1

            if current_sub_chunk:
                sub_chunks.append(" ".join(current_sub_chunk))

            for i, sub_text in enumerate(sub_chunks):
                new_chunks.append({
                    "text": sub_text,
                    "metadata": {
                        **metadata,
                        "sub_chunk": f"Part {i+1}" if len(sub_chunks) > 1 else None
                    }
                })

    return new_chunks


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

    # Step 3 & 4: Identify boundaries and split into chunks
    chunks = identify_boundaries(full_text)

    # Step 5: Assign hierarchical metadata (already done in identify_boundaries)

    # Step 6: Handle size and tables
    chunks = split_large_chunks(chunks)
    chunks = process_tables(pages, chunks)

    # Step 7: Store chunks
    save_chunks(chunks, OUTPUT_FILE)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.error(f"Error processing JSON: {str(e)}", exc_info=True)