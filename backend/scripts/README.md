# PDF Ingestion Scripts

This directory contains scripts for ingesting PDF files into the Research Assistant.

## Prerequisites

Make sure you have installed all the required dependencies:

```bash
pip install -r ../requirements.txt
```

Also, ensure that your `.env` file is properly configured with the following variables:

```
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key
GEMINI_API_KEY=your_gemini_api_key
```

## Available Scripts

### Single PDF Ingestion

To ingest a single PDF file:

```bash
python ingest_pdf.py --pdf_path /path/to/your/file.pdf [--project_id 123]
```

Arguments:
- `--pdf_path`: Path to the PDF file to ingest
- `--project_id`: (Optional) Project ID to associate with the chunks

### Batch PDF Ingestion

To ingest multiple PDF files from a directory:

```bash
python batch_ingest_pdfs.py --pdf_dir /path/to/pdf/directory [--project_id 123]
```

Arguments:
- `--pdf_dir`: Directory containing PDF files to ingest
- `--project_id`: (Optional) Project ID to associate with the chunks

## Process Flow

The ingestion process follows these steps:

1. **Parse**: Extract text and tables from the PDF
2. **Chunk**: Split the content into manageable chunks
3. **Embed**: Generate embeddings for each chunk
4. **Store**: Save the chunks and embeddings in the database

## Output

The scripts will create the following files in the `output` directory:

- `parsed_{document_id}.json`: The parsed PDF content
- `chunked_{document_id}.json`: The chunked content ready for embedding

The embedded chunks will be stored in the Supabase database in the `chunks` table. 