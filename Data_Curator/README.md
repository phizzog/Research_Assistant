# Data Curator

This tool processes and analyzes research methodology text to identify and classify content related to qualitative, quantitative, and mixed methods approaches.

## Workflow Overview

The Data Curator follows a systematic process to analyze and categorize research methodology content:

1. **Text Input Processing**
   - Accepts PDF or text input from research methodology sources
   - Stores raw input in the `input/` directory

2. **Contextualization**
   - For each page of content, builds context by considering:
     - Previous page content
     - Current page content
     - Next page content
   - This ensures classifications take into account the full context of ideas

3. **Chunking Process**
   - Splits text into manageable chunks using token-based segmentation
   - Configurable parameters:
     - Maximum tokens per chunk
     - Overlap tokens between chunks
   - Maintains context by overlapping content between chunks

4. **Classification System**
   - Each chunk is classified into one of four categories:
     - Qualitative Research
     - Quantitative Research
     - Mixed Methods
     - General Content
   - Uses predefined definitions from research methodology literature
   - Classification is performed using an LLM (Ollama) with specific prompts

5. **Output Organization**
   - Processed chunks are stored in the `output/` directory
   - Each chunk contains:
     - Original text content
     - Classification label
     - Context information

## Directory Structure

- `input/`: Raw source files
- `output/`: Processed and classified chunks
- `scripts/`: Processing and classification logic
- `prompts/`: Classification prompt templates

## Key Components

- `chunker.py`: Handles text segmentation and classification
- `definitions.py`: Contains research methodology definitions
- Configuration files for customizing processing parameters 