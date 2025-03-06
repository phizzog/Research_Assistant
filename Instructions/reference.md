1. Supabase Schema and Vector Search Function
Table: chunks
Purpose: Stores text chunks and embeddings for RAG retrieval.
Columns:
chunk_id (TEXT, PRIMARY KEY): Unique identifier (e.g., "chunk_0").
raw_text (TEXT): Original chunk text.
contextualized_text (TEXT): Enriched text with research type statement.
metadata (JSONB): Metadata (e.g., source_id, book_title, page_num, etc.).
embedding (VECTOR(768)): 768D vector embedding of contextualized_text.
Setup: Assumes pgvector is enabled (CREATE EXTENSION vector;).
Vector Search Function: match_chunks
Purpose: Retrieves the top match_count chunks most similar to a given query_embedding using cosine similarity.
SQL Definition:
sql

Collapse

Wrap

Copy
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
How It Works:
<=>: Computes cosine distance (0 = identical, 2 = opposite).
1 - (chunks.embedding <=> query_embedding): Converts to similarity (1 = identical, -1 = opposite).
Orders by distance (ascending) and limits to match_count.
Usage: Called via Supabase’s RPC endpoint with a query embedding and desired number of matches.
2. Embedding Model: nomic-ai/nomic-embed-text-v1
Details:
Source: Hugging Face.
Dimensions: 768.
Context Length: 8192 tokens.
Library: SentenceTransformer.
Role: Used to embed both the stored contextualized_text in Supabase and the incoming user query for similarity search.
Installation:
bash

Collapse

Wrap

Copy
pip install sentence-transformers
Usage Example
python

Collapse

Wrap

Copy
from sentence_transformers import SentenceTransformer
embedder = SentenceTransformer('nomic-ai/nomic-embed-text-v1', trust_remote_code=True)
query_embedding = embedder.encode("What is mixed methods research?").tolist()
3. Backend Adjustments
Your frontend currently calls Gemini directly or via a simple backend. To integrate Supabase embeddings, you’ll need a backend API to:

Receive the query from the frontend.
Generate a query embedding.
Retrieve relevant chunks from Supabase.
Send the query and context to Gemini.
Return the response to the frontend.
Example Backend (FastAPI)
File: backend.py

python

Collapse

Wrap

Copy
import os
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from supabase import create_client, Client
from sentence_transformers import SentenceTransformer
import google.generativeai as genai
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI()

# CORS setup (adjust origins as needed)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Supabase setup
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Embedding model
EMBEDDING_MODEL = "nomic-ai/nomic-embed-text-v1"
embedder = SentenceTransformer(EMBEDDING_MODEL, trust_remote_code=True)

# Google Gemini setup
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=GEMINI_API_KEY)
gemini_model = genai.GenerativeModel('gemini-pro')  # Adjust model name as needed

# Retrieve context from Supabase
def retrieve_context(query: str, top_k: int = 5) -> str:
    query_embedding = embedder.encode([query]).tolist()[0]
    response = supabase.rpc("match_chunks", {
        "query_embedding": query_embedding,
        "match_count": top_k
    }).execute()
    if not response.data:
        logger.warning("No matching chunks found")
        return ""
    relevant_chunks = [item["contextualized_text"] for item in response.data]
    context = "\n\n".join(relevant_chunks)
    logger.info(f"Retrieved {len(relevant_chunks)} chunks for query: {query}")
    return context

# Generate response with Gemini
def generate_response(query: str, context: str) -> str:
    prompt = f"""
    ### Task:
    Answer the query using the provided context from a research design book. Provide a concise, accurate response based on the context.

    ### Context:
    {context}

    ### Query:
    {query}
    """
    try:
        response = gemini_model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        logger.error(f"Gemini API error: {e}")
        return "Error generating response"

@app.post("/query")
async def handle_query(request: Request):
    data = await request.json()
    query = data.get("query", "")
    if not query:
        return {"error": "Query is required"}
    
    context = retrieve_context(query)
    if not context:
        return {"answer": "No relevant context found"}
    
    answer = generate_response(query, context)
    return {"answer": answer}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
Deployment Notes
Run: uvicorn backend:app --host 0.0.0.0 --port 8000.
Dependencies: Install via pip install fastapi uvicorn supabase sentence-transformers google-generativeai python-dotenv.
Environment: Add to .env:
text

Collapse

Wrap

Copy
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_KEY=your-service-role-key
GEMINI_API_KEY=your-gemini-api-key
4. Frontend Adjustments
Assuming your current frontend sends queries to Gemini directly or via a simple backend, you’ll modify it to call the new /query endpoint.

Example: React Frontend
File: src/components/QueryForm.js (modify your existing component)

jsx

Collapse

Wrap

Copy
import React, { useState } from 'react';
import axios from 'axios';

const QueryForm = () => {
  const [query, setQuery] = useState('');
  const [response, setResponse] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const res = await axios.post('http://your-backend-ip:8000/query', { query });
      setResponse(res.data.answer);
    } catch (err) {
      setError('Failed to fetch response. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <form onSubmit={handleSubmit}>
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Enter your query"
          style={{ width: '300px', padding: '8px' }}
        />
        <button type="submit" disabled={loading} style={{ padding: '8px 16px' }}>
          {loading ? 'Loading...' : 'Ask'}
        </button>
      </form>
      {error && <p style={{ color: 'red' }}>{error}</p>}
      {response && (
        <div>
          <strong>Answer:</strong>
          <p>{response}</p>
        </div>
      )}
    </div>
  );
};

export default QueryForm;
Key Changes
API Endpoint: Replace the old Gemini API call with a POST to http://your-backend-ip:8000/query.
Response Handling: Expect a JSON response with an "answer" field instead of Gemini’s raw format.
5. Deployment Considerations (Optional)
If deploying on DigitalOcean:

Droplet: Use a 2GB RAM, 1 vCPU instance for small-scale use.
Setup:
Install Python and dependencies (pip install -r requirements.txt).
Copy your .env file and scripts.
Run the backend: uvicorn backend:app --host 0.0.0.0 --port 8000.
Frontend: Host separately (e.g., Netlify) or on the same Droplet with Nginx serving the build (npm run build).
6. Testing the Integration
Start Backend:
bash

Collapse

Wrap

Copy
python backend.py
Run Frontend:
bash

Collapse

Wrap

Copy
npm start
Test Queries:
"What is mixed methods research?"
"How does qualitative research differ from quantitative?"
Check if responses use Supabase context and align with your book.