# Research Assistant Backend

This is the backend for the Research Assistant application, which provides RAG (Retrieval-Augmented Generation) capabilities using Supabase for vector storage and Gemini for text generation.

## Setup

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Create a `.env` file based on `.env.example` and fill in your credentials:
   ```
   SUPABASE_URL=https://your-project-id.supabase.co
   SUPABASE_KEY=your-service-role-key
   GEMINI_API_KEY=your-gemini-api-key
   ```

3. Make sure your Supabase database has the required schema:
   - A `chunks` table with the following columns:
     - `chunk_id` (TEXT, PRIMARY KEY): Unique identifier
     - `raw_text` (TEXT): Original chunk text
     - `contextualized_text` (TEXT): Enriched text with research type statement
     - `metadata` (JSONB): Metadata (e.g., source_id, book_title, page_num, etc.)
     - `embedding` (VECTOR(768)): 768D vector embedding of contextualized_text

4. Ensure the `match_chunks` function is created in your Supabase database:
   ```sql
   CREATE OR REPLACE FUNCTION match_chunks(query_embedding VECTOR(768), match_count INT)
   RETURNS TABLE (
       chunk_id TEXT,
       raw_text TEXT,
       contextualized_text TEXT,
       metadata JSONB,
       similarity FLOAT
   ) AS $$
   BEGIN
       RETURN QUERY
       SELECT chunks.chunk_id, chunks.raw_text, chunks.contextualized_text, chunks.metadata,
              1 - (chunks.embedding <=> query_embedding) AS similarity
       FROM chunks
       ORDER BY chunks.embedding <=> query_embedding
       LIMIT match_count;
   END;
   $$ LANGUAGE plpgsql;
   ```

## Running the Backend

Start the FastAPI server:

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

## API Endpoints

- `POST /query`: Query the system with a text prompt
- `POST /chat`: Send a message in a chat context
- `POST /upload`: Upload a file for analysis
- `GET /health`: Health check endpoint

## Example Usage

```bash
# Query endpoint
curl -X POST "http://localhost:8000/query" \
  -H "Content-Type: application/json" \
  -d '{"query": "What is mixed methods research?", "top_k": 5}'

# Chat endpoint
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{"message": "What is mixed methods research?", "chat_history": [{"role": "user", "content": "Hello"}, {"role": "assistant", "content": "Hi there! How can I help you with your research today?"}]}'
``` 