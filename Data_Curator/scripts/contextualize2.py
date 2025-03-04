import json
import requests
import logging
from typing import Dict, List

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("research_design_processing.log"),  # Log to a file
        logging.StreamHandler()  # Also log to console
    ]
)
logger = logging.getLogger(__name__)

# Assuming Ollama is running locally at http://localhost:11434/api/generate
OLLAMA_ENDPOINT = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "llama3.1:8b"  # Replace with your preferred model

# Load the JSON document
input_file = r"C:\Users\kenny\OneDrive\code\Research-Assistant\Data_Curator\output\chunked_examplename2.json"
logger.info(f"Loading JSON document from {input_file}")
try:
    with open(input_file, "r") as f:
        document = json.load(f)
    logger.info("JSON document loaded successfully")
except Exception as e:
    logger.error(f"Failed to load JSON document: {e}")
    raise

# Definitions from Creswell's book
DEFINITIONS = {
    "qualitative": (
        "Qualitative research is an approach for exploring and understanding "
        "the meaning individuals or groups ascribe to a social or human problem. "
        "The research process involves emerging questions and procedures, data typically "
        "collected in the participant's setting, data analysis inductively building from "
        "particulars to general themes, and the researcher making interpretations of the "
        "meaning of the data. The final written report has a flexible structure. Those who "
        "engage in this form of inquiry use an inductive style building from data to themes "
        "and a focus on individual meaning, and emphasize the importance of reporting the "
        "complexity of a situation."
    ),
    "quantitative": (
        "Quantitative research is an approach for testing objective theories by "
        "examining the relationship among variables or a comparison among groups. "
        "These variables, in turn, can be measured, typically on instruments, so that "
        "numbered data can be analyzed using statistical procedures. The final written "
        "report has a set structure comprising an introduction, methods, results, and "
        "discussion. Quantitative researchers test theories deductively, build into a "
        "study protections against bias, control for alternative or counterfactual "
        "explanations, and seek to generalize and replicate the findings."
    ),
    "mixed": (
        "Mixed methods research is an approach to inquiry involving collecting both "
        "quantitative and qualitative data, using a specific procedure or design, "
        "combining (or integrating) the two forms of data within the design, and "
        "drawing conclusions (metainferences) about the insight to emerge from the "
        "combined databases. This description emphasizes a methods perspective focused "
        "on understanding mixed methods research from its data collection, data analysis, "
        "and interpretation. Also, in mixed methods a researcher brings philosophical "
        "assumptions and theories that inform the conduct of the research."
    )
}

def determine_context(chunk: Dict, document: List[Dict]) -> str:
    """
    Dynamically determine relevant context for a chunk based on its metadata and content.
    """
    metadata = chunk["metadata"]
    raw_text = chunk["text"]
    logger.debug(f"Determining context for chunk: {raw_text[:50]}...")

    # Base context from the book's preface for general background
    base_context_chunks = [c["text"] for c in document if c["metadata"]["section"] == "PREFACE"]
    base_context = "\n".join(base_context_chunks)

    # Add context based on part (e.g., Part I or Part II)
    part_context = ""
    if metadata["part"]:
        part_context_chunks = [
            c["text"] for c in document 
            if c["metadata"]["part"] == metadata["part"] and c["text"] != raw_text
        ]
        part_context = "\n".join(part_context_chunks[:3])  # Limit to 3 chunks for brevity

    # Add chapter-specific context if available
    chapter_context = ""
    if metadata["chapter"]:
        chapter_context_chunks = [
            c["text"] for c in document 
            if c["metadata"]["chapter"] == metadata["chapter"] and c["text"] != raw_text
        ]
        chapter_context = "\n".join(chapter_context_chunks[:2])  # Limit to 2 chunks

    # Combine contexts
    full_context = f"{base_context}\n\n{part_context}\n\n{chapter_context}".strip()
    logger.debug(f"Context determined, length: {len(full_context)} characters")
    return full_context

def get_ollama_response(prompt: str) -> str:
    """
    Send prompt to Ollama and return the response.
    """
    logger.debug(f"Sending prompt to Ollama, length: {len(prompt)} characters")
    payload = {
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False
    }
    try:
        response = requests.post(OLLAMA_ENDPOINT, json=payload)
        response.raise_for_status()
        logger.debug("Ollama response received successfully")
        return response.json()["response"]
    except requests.RequestException as e:
        logger.error(f"Ollama API error: {e}")
        raise Exception(f"Ollama API error: {e}")

def classify_chunk(raw_text: str) -> str:
    """
    Classify the chunk using Ollama and the classification prompt.
    """
    logger.info(f"Classifying chunk: {raw_text[:50]}...")
    classification_prompt = f"""
You are tasked with classifying a given text as either 'qualitative', 'quantitative', 'mixed', or 'general' research. To help you make this classification, please use the following definitions:

Qualitative Research:
<qualitative_def>
{DEFINITIONS["qualitative"]}
</qualitative_def>

Quantitative Research:
<quantitative_def>
{DEFINITIONS["quantitative"]}
</quantitative_def>

Mixed Methods:
<mixed_def>
{DEFINITIONS["mixed"]}
</mixed_def>

Now, carefully read and analyze the following text:

<text_to_classify>
{raw_text}
</text_to_classify>

Based on the definitions provided and your analysis of the text, determine which category it best fits into. Consider the following:

1. Does the text primarily discuss non-numerical data, experiences, or interpretations?
2. Does it focus on numerical data, statistical analysis, or measurable variables?
3. Does it combine both qualitative and quantitative elements?
4. If it doesn't clearly fit into any of these categories, it may be classified as 'general'.

Provide your reasoning for the classification in <reasoning> tags. Your reasoning should be concise but clear, explaining why you believe the text fits best into the chosen category.

After providing your reasoning, give your final classification as a single word response. Use ONLY ONE of these exact words: qualitative, quantitative, mixed, or general.

Your complete response should be structured as follows:

<reasoning>
[Your reasoning here]
</reasoning>

<classification>
[Your one-word classification here]
</classification>
"""
    response = get_ollama_response(classification_prompt)
    try:
        classification = response.split("<classification>")[1].split("</classification>")[0].strip()
        logger.info(f"Chunk classified as: {classification}")
        return classification
    except IndexError as e:
        logger.error(f"Failed to parse classification from response: {e}")
        return "general"  # Default fallback

def contextualize_chunk(chunk: Dict, context: str, classification: str) -> str:
    """
    Contextualize a single chunk using the provided prompt and Ollama.
    """
    chunk_id = f"chunk_{document['chunks'].index(chunk)}"
    raw_text = chunk["text"]
    logger.info(f"Contextualizing chunk: {raw_text[:50]}... with classification: {classification}")

    classification_instructions = {
        "qualitative": "Focus on enriching descriptions, participant perspectives, and qualitative methodologies.",
        "quantitative": "Focus on enriching statistical methods, variables, and quantitative designs.",
        "mixed": "Focus on integrating qualitative and quantitative elements and mixed methods procedures.",
        "general": "Provide a broad enhancement relevant to research design principles."
    }

    prompt = f"""
You are tasked with analyzing and enriching a text chunk using provided context. Your goal is to create a more informative version of the original text by integrating relevant information from the context while maintaining the original meaning.

First, review the following context carefully. This information will help you understand the broader topic and enrich the text chunk:

<context>
{context}
</context>

Now, you will be given a chunk of text to analyze and enrich. Here are the details:

<chunk_id>{chunk_id}</chunk_id>

<raw_text>
{raw_text}
</raw_text>

<classification>{classification}</classification>

{classification_instructions[classification]}

To create the contextualized chunk:
1. Carefully read the raw text and understand its main points.
2. Identify key concepts, terms, or ideas in the raw text that could benefit from additional context.
3. Refer back to the provided context and find relevant information that can enhance the understanding of the raw_text.
4. Integrate this contextual information into the raw_text, expanding on important points, clarifying concepts, or providing background information as needed.
5. Ensure that the original meaning and intent of the raw_text are preserved while adding depth and clarity.
6. Consider the classification of the text when enriching it, focusing on aspects relevant to that type of research.

Your output should be formatted exactly as follows:

<chunk_id>{chunk_id}</chunk_id>
<raw_text>{raw_text}</raw_text>
<contextualized_chunk>
[Place your enriched version here. Integrate relevant context to enhance understanding while maintaining the original meaning.]
</contextualized_chunk>
"""
    response = get_ollama_response(prompt)
    logger.info(f"Chunk contextualized successfully: {raw_text[:50]}...")
    return response

def process_chunks(document: Dict) -> List[Dict]:
    """
    Process all chunks: classify, contextualize, and parse the enriched response.
    """
    enriched_chunks = []
    total_chunks = len(document["chunks"])
    logger.info(f"Starting processing of {total_chunks} chunks")

    for i, chunk in enumerate(document["chunks"]):
        logger.info(f"Processing chunk {i + 1}/{total_chunks}")

        # Step 1: Classify the chunk
        classification = classify_chunk(chunk["text"])
        
        # Step 2: Determine context and contextualize
        context = determine_context(chunk, document["chunks"])
        enriched_response = contextualize_chunk(chunk, context, classification)
        
        # Step 3: Parse the enriched_response
        try:
            chunk_id = enriched_response.split("<chunk_id>")[1].split("</chunk_id>")[0]
            raw_text = enriched_response.split("<raw_text>")[1].split("</raw_text>")[0]
            contextualized_text = enriched_response.split("<contextualized_chunk>")[1].split("</contextualized_chunk>")[0].strip("[]")
            logger.debug(f"Parsed chunk {chunk_id} successfully")
        except IndexError as e:
            logger.warning(f"Error parsing enriched response for chunk: {chunk['text'][:50]}... - {e}")
            chunk_id = f"chunk_{document['chunks'].index(chunk)}"
            raw_text = chunk["text"]
            contextualized_text = "Error parsing enriched response"
        
        # Step 4: Structure the enriched chunk
        enriched_chunk = {
            "chunk_id": chunk_id,
            "raw_text": raw_text,
            "classification": classification,
            "contextualized_text": contextualized_text,
            "metadata": chunk["metadata"]
        }
        enriched_chunks.append(enriched_chunk)
    
    logger.info(f"Completed processing {total_chunks} chunks")
    return enriched_chunks

# Process the chunks
try:
    enriched_data = process_chunks(document)
except Exception as e:
    logger.error(f"Error during chunk processing: {e}")
    raise

# Save to file
output_file = "enriched_chunks.json"
logger.info(f"Saving enriched chunks to {output_file}")
try:
    with open(output_file, "w") as f:
        json.dump(enriched_data, f, indent=2)
    logger.info(f"Enriched chunks saved successfully to {output_file}")
except Exception as e:
    logger.error(f"Failed to save enriched chunks: {e}")
    raise

print("Chunks classified, enriched, parsed, and saved to 'enriched_chunks.json'.")

# Optional: Supabase integration
# Uncomment and configure if you want to upload to Supabase
"""
from supabase import create_client, Client

supabase_url = "your-supabase-url"
supabase_key = "your-supabase-key"
supabase: Client = create_client(supabase_url, supabase_key)

logger.info("Uploading data to Supabase")
for chunk in enriched_data:
    data = {
        "chunk_id": chunk["chunk_id"],
        "raw_text": chunk["raw_text"],
        "contextualized_text": chunk["contextualized_text"],
        "classification": chunk["classification"],
        "metadata": chunk["metadata"]
    }
    try:
        supabase.table("chunks").insert(data).execute()
        logger.debug(f"Uploaded chunk {chunk['chunk_id']} to Supabase")
    except Exception as e:
        logger.error(f"Failed to upload chunk {chunk['chunk_id']} to Supabase: {e}")

logger.info("Data uploaded to Supabase successfully")
print("Data uploaded to Supabase.")
"""