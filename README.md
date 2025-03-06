# Research Assistant

An AI-powered research assistant that helps users with research methodology, using RAG (Retrieval-Augmented Generation) with Supabase for vector storage and Gemini for text generation.

## Project Structure

- `frontend/`: Next.js frontend application
- `backend/`: FastAPI backend application
- `Data_Curator/`: Tools for processing and uploading research data

## Setup

### Backend Setup

1. Navigate to the backend directory:
   ```bash
   cd backend
   ```

2. Create a virtual environment and activate it:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Create a `.env` file based on `.env.example` and fill in your credentials:
   ```
   SUPABASE_URL=https://your-project-id.supabase.co
   SUPABASE_KEY=your-service-role-key
   GEMINI_API_KEY=your-gemini-api-key
   ```

5. Make sure your Supabase database has the required schema and functions as described in the backend README.

6. Start the backend server:
   ```bash
   uvicorn main:app --host 0.0.0.0 --port 8000 --reload
   ```

### Frontend Setup

1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Create a `.env.local` file based on `.env.local.example` and fill in your credentials:
   ```
   NEXT_PUBLIC_GEMINI_API_KEY=your-gemini-api-key
   NEXT_PUBLIC_SUPABASE_URL=your-supabase-url
   NEXT_PUBLIC_SUPABASE_ANON_KEY=your-supabase-anon-key
   NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
   ```

4. Start the frontend development server:
   ```bash
   npm run dev
   ```

5. Open your browser and navigate to `http://localhost:3000`

## Supabase Setup

1. Create a new Supabase project
2. Enable the pgvector extension:
   ```sql
   CREATE EXTENSION vector;
   ```

3. Create the chunks table:
   ```sql
   CREATE TABLE chunks (
     chunk_id TEXT PRIMARY KEY,
     raw_text TEXT,
     contextualized_text TEXT,
     metadata JSONB,
     embedding VECTOR(768)
   );
   ```

4. Create the match_chunks function:
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

## Features

- Research methodology recommendation based on project details and questionnaire
- Chat interface for asking questions about research methodology
- RAG-powered responses using content from research design books
- File upload for analysis

## Technologies Used

- **Frontend**: Next.js, React, TypeScript, Tailwind CSS
- **Backend**: FastAPI, Python
- **Vector Database**: Supabase with pgvector
- **Embedding Model**: nomic-ai/nomic-embed-text-v1
- **LLM**: Google Gemini

## License

[MIT License](LICENSE)

## Abstract
Development of Research Assistant with Adaptive AI Software: Enhancing Academic Research Efficiency 

Simon Derstine, Kenny Snyder, Elina Ivanova, Patrick Rockow 

Organizing and structuring academic research can be complex, and researchers often struggle with handling large amounts of information, developing a clear framework, and extracting key insights from various sources. The AI research assistant software streamlines this process by using a framework suggested in the book: "Research Design: Qualitative and Quantitative, and Mixed Methods Approaches". The app features a conversational interface that walks a user through a step-by-step process with guided questions tailored to the type of research being conducted.  

As students' progress through each stage, the AI Assistant uses carefully designed questions to guide them in developing research questions, creating outlines, conducting literature reviews, and structuring their arguments effectively.  The system leverages a Large Language Model (LLM) combined with Retrieval-Augmented Generation (RAG) to provide contextually relevant guidance based on the research book's framework. This architecture ensures that the assistant's responses are both grounded in established research methodology and dynamically adapted to each user's specific research context. 