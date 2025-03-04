import json
import re
import logging
from typing import List, Dict, Any
import tiktoken
import requests
from collections import defaultdict

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# Constants
MAX_TOKENS_PER_CHUNK = 700
OLLAMA_BASE_URL = "http://localhost:11434/api/generate"
MODEL = "llama3.1:8b"
INPUT_FILE = r"C:\Users\kenny\OneDrive\code\Research-Assistant\Data_Curator\input\test.json"
OUTPUT_FILE = r"C:\Users\kenny\OneDrive\code\Research-Assistant\Data_Curator\output\chapter_topics.json"

# Regex patterns
CHAPTER_PATTERN = re.compile(r'^CHAPTER \d+ .+$', re.MULTILINE)
SECTION_PATTERN = re.compile(r'^[A-Z\s\d.,:;!?()\-—–]+$', re.MULTILINE)
PART_PATTERN = re.compile(r'^PART [I]+ .+$', re.MULTILINE)

# Token counting setup
ENCODING = tiktoken.get_encoding("cl100k_base")

def check_ollama_status():
    """Check if Ollama is running on the local device."""
    logger.info("Checking if Ollama is running locally...")
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        if response.status_code == 200:
            models = response.json().get('models', [])
            logger.info(f"Ollama is running. Available models: {[m['name'] for m in models if 'name' in m]}")
            model_names = [m['name'] for m in models if 'name' in m]
            if MODEL.split(':')[0] not in ' '.join(model_names):
                logger.warning(f"Model '{MODEL}' may not be available. Please pull it using 'ollama pull {MODEL}'")
            return True
        else:
            logger.error(f"Ollama returned status code {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        logger.error("Failed to connect to Ollama. Is it running?")
        logger.info("To start Ollama, run: ollama serve")
        return False
    except Exception as e:
        logger.error(f"Error checking Ollama status: {str(e)}")
        return False

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
    """Identify chapter/section boundaries and split into paragraph-based chunks."""
    logger.info("Identifying boundaries and splitting into paragraphs")
    chunks = []
    current_part = None
    current_chapter = None
    current_section = None
    current_text = ""

    lines = full_text.split('\n')
    for line in lines:
        line = line.strip()

        part_match = PART_PATTERN.match(line)
        if part_match:
            if current_text.strip():
                chunks.extend(split_into_paragraph_chunks(current_text, current_part, current_chapter, current_section))
            current_part = line
            current_chapter = None
            current_section = None
            current_text = ""
            continue

        chapter_match = CHAPTER_PATTERN.match(line)
        if chapter_match:
            if current_text.strip():
                chunks.extend(split_into_paragraph_chunks(current_text, current_part, current_chapter, current_section))
            current_chapter = line
            current_section = None
            current_text = line + "\n"
            continue

        section_match = SECTION_PATTERN.match(line)
        if section_match and len(line) > 10 and not line.startswith("PART "):
            if current_text.strip():
                chunks.extend(split_into_paragraph_chunks(current_text, current_part, current_chapter, current_section))
            current_section = line
            current_text = line + "\n"
            continue

        current_text += line + "\n"

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

def get_chapter_text(chunks: List[Dict[str, Any]]) -> Dict[str, str]:
    """Group chunks by chapter and concatenate their text."""
    logger.info("Grouping chunks by chapter")
    chapter_texts = defaultdict(str)
    for chunk in chunks:
        chapter = chunk['metadata']['chapter']
        if chapter:
            chapter_texts[chapter] += chunk['text'] + "\n\n"
    return chapter_texts

def identify_topics(chapter_text: str, chapter: str) -> List[str]:
    """Use Ollama with Llama 3.1 8B to identify exactly 5 topics in a chapter's text, returned in XML tags."""
    logger.info(f"Identifying topics for {chapter}")
    prompt = (
        f"Analyze the following text from {chapter} and identify exactly 5 main topics discussed. "
        "Return the topics as concise names (e.g., 'Philosophical Worldviews', 'Research Designs'), "
        "with no additional explanations, numbering, or text outside the specified XML structure. "
        "Wrap each topic in an XML <topic> tag, and enclose the entire list in a <topics> tag. "
        "Follow this exact format:\n"
        "<topics>\n"
        "  <topic>First Topic</topic>\n"
        "  <topic>Second Topic</topic>\n"
        "  <topic>Third Topic</topic>\n"
        "  <topic>Fourth Topic</topic>\n"
        "  <topic>Fifth Topic</topic>\n"
        "</topics>\n"
        "Ensure there are exactly 5 topics, and do not include any text before or after the XML structure.\n\n"
        f"Text:\n{chapter_text[:32000]}\n\n"
    )

    payload = {
        "model": MODEL,
        "prompt": prompt,
        "stream": False
    }
    try:
        response = requests.post(OLLAMA_BASE_URL, json=payload, timeout=60)
        response.raise_for_status()
        response_text = response.json().get('response', '').strip()

        # Log the raw response for debugging
        logger.debug(f"Raw response for {chapter}: {response_text}")

        # Parse XML to extract topics
        import xml.etree.ElementTree as ET
        try:
            root = ET.fromstring(response_text)
            topics = [elem.text.strip() for elem in root.findall('topic') if elem.text]
            logger.info(f"Topics identified for {chapter}: {topics}")
            # Ensure exactly 5 topics; pad with placeholders or truncate if necessary
            if len(topics) < 5:
                topics.extend([f"Topic {i+1}" for i in range(len(topics), 5)])
            return topics[:5]
        except ET.ParseError as e:
            logger.error(f"Failed to parse XML response for {chapter}: {str(e)}")
            # Fallback: Attempt to extract topics from response manually
            topics = extract_topics_fallback(response_text, chapter)
            return topics
    except Exception as e:
        logger.error(f"Failed to identify topics for {chapter}: {str(e)}")
        return [f"{chapter} Topic {i+1}" for i in range(5)]

def extract_topics_fallback(response_text: str, chapter: str) -> List[str]:
    """Fallback method to extract 5 topics from a non-XML response."""
    logger.info(f"Attempting fallback topic extraction for {chapter}")
    lines = [line.strip() for line in response_text.split('\n') if line.strip()]
    topics = []
    
    # Look for lines that seem like topic names (e.g., no numbers, short phrases)
    for line in lines:
        # Skip lines that look like markup or are too long to be a topic
        if not line.startswith('<') and not line.startswith('>') and len(line) < 50:
            # Clean up common prefixes or formatting
            cleaned_line = re.sub(r'^\d+\.\s*|\*\s*|-+\s*', '', line).strip()
            if cleaned_line and cleaned_line not in topics:
                topics.append(cleaned_line)
    
    # Ensure exactly 5 topics
    if len(topics) < 5:
        topics.extend([f"Topic {i+1}" for i in range(len(topics), 5)])
    logger.info(f"Fallback topics for {chapter}: {topics[:5]}")
    return topics[:5]

def save_chapter_topics(chapter_topics: Dict[str, List[str]], output_file: str):
    """Save the chapter topics to a JSON file."""
    logger.info(f"Saving chapter topics to {output_file}")
    output_data = {
        "chapters": chapter_topics
    }
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2)
    logger.info(f"Saved {len(chapter_topics)} chapters with topics to {output_file}")

def main():
    """Main function to process the document and save chapter topics."""
    try:
        if not check_ollama_status():
            logger.error("Ollama is not running. Please start it before running this script.")
            logger.info("You can start Ollama by running 'ollama serve' in a command prompt.")
            return
            
        # Load the JSON data
        data = load_json(INPUT_FILE)
        pages = data['pages']

        # Concatenate page texts
        full_text = concatenate_page_texts(pages)

        # Identify boundaries and split into paragraph-based chunks
        chunks = identify_boundaries_and_paragraphs(full_text)

        # Process tables
        chunks = process_tables(pages, chunks)

        # Group by chapter and identify topics
        chapter_texts = get_chapter_text(chunks)
        chapter_topics = {}
        for chapter, text in chapter_texts.items():
            chapter_topics[chapter] = identify_topics(text, chapter)

        # Save chapter topics to JSON
        save_chapter_topics(chapter_topics, OUTPUT_FILE)
    except Exception as e:
        logger.error(f"Error processing JSON: {str(e)}", exc_info=True)

if __name__ == "__main__":
    main()