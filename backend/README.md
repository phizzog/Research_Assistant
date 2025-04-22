# Research Assistant Backend

A powerful backend API for the Research Assistant application, designed to guide users through the research process based on "Research Design: Qualitative, Quantitative, and Mixed Methods Approaches" by John W. Creswell and J. David Creswell. This system provides structured guidance, document management, and AI-powered research assistance.

## System Overview

The Research Assistant is a comprehensive system that:

1. Guides users through a structured 10-step research process
2. Provides intelligent assistance based on research methodology best practices
3. Uses Retrieval-Augmented Generation (RAG) to provide context-specific advice
4. Manages projects, documents, and research progress in a Supabase database
5. Integrates with Google Gemini Flash 2.0 and Nomic Embed API for AI capabilities

## Architecture

The backend follows a clean, modular architecture:

- **API Layer** (`app/api/`): FastAPI routes and endpoint handlers
- **Core Layer** (`app/core/`): Configuration, database connections, AI services
- **Models Layer** (`app/models/`): Pydantic models and schemas
- **Services Layer** (`app/services/`): Business logic, PDF processing, RAG implementation
- **Utils Layer** (`app/utils/`): Utility functions and error handlers

## Features

- **Structured Research Guidance**: 10-step process covering research design, literature review, methodology, and more
- **AI-Powered Assistance**: Google Gemini integration for intelligent responses based on research methodology
- **Document Management**: PDF ingestion, processing, and semantic search
- **Conversational Interface**: Maintain chat history and provide contextual guidance
- **Project Management**: Track progress through research steps

## Setup and Installation

### Prerequisites

- Python 3.9+
- Supabase account
- Google Gemini API key
- Nomic Embed API access
- Tavily API key (for search capabilities)

### Installation

1. Clone the repository

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Create a `.env` file based on `.env.example` and configure your environment variables:
   ```
   SUPABASE_URL=https://your-project-id.supabase.co
   SUPABASE_KEY=your-service-role-key
   GEMINI_API_KEY=your-gemini-api-key
   TAVILY_API_KEY=your-tavily-api-key
   ```

5. Start the backend server:
   ```bash
   python -m main
   ```

## API Endpoints

The backend exposes the following RESTful endpoints:

### Query and Chat

- `POST /query`: Submit a single query for AI-assisted response
  - Parameters: `query`, `top_k` (optional), `project_id` (optional), `selected_document_ids` (optional)
  - Returns: AI-generated response based on query context

- `POST /chat`: Chat with the research assistant
  - Parameters: `messages` (list of previous messages), `project_id` (optional), `top_k` (optional)
  - Returns: AI response maintaining conversation context

- `POST /chat-with-project`: Chat with context from a specific project
  - Parameters: `project_id`, `message`, `previous_messages` (optional)
  - Returns: AI response with project-specific context

### Document Management

- `POST /ingest`: Upload and process a PDF file
  - Parameters: 
    - `file`: PDF file
    - `project_id` (optional): Associated project ID
    - `user_id` (optional): User ID
    - `process_type` (optional): Processing level ("full", "parse_only", "chunk_only", "embed_only")
    - `simple_mode` (optional): Boolean for simplified response
    - `custom_document_name` (optional): Custom name for the document
  - Returns: Processing status and document details

- `POST /batch-ingest`: Upload and process multiple PDF files
  - Parameters: 
    - `files`: List of PDF files
    - `project_id` (optional): Associated project ID
    - `user_id` (optional): User ID
  - Returns: List of processing results for each file

### Research Assistance

- `POST /suggest-sources`: Get source suggestions for a research topic
  - Parameters: `query`, `project_id` (optional)
  - Returns: Relevant sources and suggestions

- `POST /identify-gaps`: Identify research gaps based on existing documents
  - Parameters: `query`, `project_id` (optional)
  - Returns: Analysis of research gaps

- `POST /search-for-gap`: Search external sources for research gap information
  - Parameters: `query`, `project_id` (optional)
  - Returns: External search results relevant to the gap

### System

- `GET /health`: Health check endpoint for monitoring
  - Returns: Server status and timestamp

## Database Schema

The application uses Supabase with the following main tables:

### Projects Table

Stores research project information:

```
projects
├── project_id (PK): integer
├── project_name: varchar(100)
├── description: text
├── user_id: uuid
├── created_at: timestamp
├── research_type: enum
└── learning_objective: text
```

### Sources Table

Stores embedded document chunks for RAG:

```
sources
├── id (PK): integer
├── source_id: text
├── chunk_id: text
├── raw_text: text
├── embedding: vector
├── metadata: jsonb
├── created_at: timestamp
└── project_id: integer
```

### Chat Messages Table

Stores chat history:

```
chatmessages
├── message_id (PK): integer
├── project_id: integer
├── user_id: uuid
├── message_text: text
├── sender_type: enum
└── sent_at: timestamp
```

### Documents Table

Stores uploaded PDF information:

```
pdfs
├── pdf_id (PK): integer
├── project_id: integer
├── file_name: varchar(100)
├── file_path: varchar(255)
├── file_size: integer
├── raw_text: text
└── upload_date: timestamp
```

### Research Steps Tables

Tracks progress through research steps:

```
questions
├── question_id (PK): integer
└── question_text: text

choices
├── choice_id (PK): integer
├── question_id: integer
├── choice_text: text
└── description: text

userresponses
├── response_id (PK): integer
├── user_id: uuid
├── project_id: integer
├── question_id: integer
└── choice_id: integer
```

## PDF Ingestion Pipeline

The application processes PDFs through a sophisticated pipeline:

1. **PDF Parsing**: Extract text and structure from PDF documents
   - Uses `pdfplumber` and other tools to extract text
   - Maintains document structure and formatting where possible

2. **Content Chunking**: Split content into semantic chunks
   - Chunks are created based on semantic boundaries
   - Optimized size for embedding and retrieval
   - Metadata preserved for context

3. **Embedding Generation**: Create vector embeddings for each chunk
   - Uses Nomic Embed API for high-quality embeddings
   - Embeddings enable semantic search and retrieval

4. **Database Storage**: Store chunks and embeddings in Supabase
   - Linked to projects and users
   - Optimized for vector similarity search

### Using the Ingestion Pipeline

#### Via API

Upload documents through the `/ingest` or `/batch-ingest` endpoints.

#### Via Command-Line

```bash
# Single PDF ingestion
python scripts/ingest_pdf.py --pdf_path /path/to/your/file.pdf --project_id 123

# Batch PDF ingestion
python scripts/batch_ingest_pdfs.py --pdf_dir /path/to/pdf/directory --project_id 123
```

## RAG Implementation

The Research Assistant uses a sophisticated RAG (Retrieval-Augmented Generation) system:

1. **Document Processing**: Documents are processed, chunked, and embedded
2. **Query Enhancement**: User queries are expanded for better semantic matching
3. **Contextual Retrieval**: Most relevant chunks are retrieved based on semantic similarity
4. **Content Generation**: Google Gemini model generates responses with retrieved context
5. **Project Contextualization**: All queries are enriched with project-specific information

## Development

### Adding New Features

1. Define new models in `app/models/schemas.py`
2. Implement business logic in `app/services/`
3. Add new API endpoints in `app/api/routes.py`
4. Update configuration if needed in `app/core/config.py`

### Error Handling

The application uses a centralized error handling system:

- `app/utils/error_handlers.py` contains exception handlers
- `AppException` class for application-specific exceptions
- Consistent error responses across the API

### Logging

Comprehensive logging is configured using both Python's standard logging and Loguru:

- Request/response logging
- Error tracking
- Performance monitoring
- Debug information

## Testing

To run tests:

```bash
pytest
```

The `tests/` directory contains:
- Unit tests for all services
- Integration tests for API endpoints
- Utility tests for helper functions

Manual testing scripts are also provided:
- `test_ingest.py`: Tests PDF ingestion
- `test_project_id.py`: Tests project ID storage

## Deployment

### Docker Deployment

The application can be deployed using Docker:

```bash
docker build -t research-assistant-backend .
docker run -p 8000:8000 --env-file .env research-assistant-backend
```

### Environment Configuration

Configure the following environment variables:

- `SUPABASE_URL`: Your Supabase project URL
- `SUPABASE_KEY`: Your Supabase service role key
- `GEMINI_API_KEY`: Your Google Gemini API key
- `TAVILY_API_KEY`: Your Tavily API key
- `API_HOST`: Host to bind the API server (default: 0.0.0.0)
- `API_PORT`: Port for the API server (default: 8000)

## Security Considerations

- API keys are stored as environment variables, never in code
- User authentication is handled through Supabase
- Project data is isolated by project_id and user_id
- Input validation is performed using Pydantic models
- Error handling prevents sensitive information leakage

## Performance Optimization

- Embedding generation is optimized for speed and quality
- Database queries use indexes for efficient retrieval
- Caching is implemented for frequent operations
- Large file processing is handled with streaming
- API responses are optimized for minimal payload size

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests to ensure everything works
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details. 