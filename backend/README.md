# Research Assistant Backend

This is the backend API for the Research Assistant application, built with FastAPI and Python.

## Architecture

The backend follows a modular architecture for better maintainability and separation of concerns:

- **API Layer** (`app/api/`): Handles HTTP requests and responses
- **Core Layer** (`app/core/`): Contains core functionality like configuration, database connections, and AI services
- **Models Layer** (`app/models/`): Defines data models and schemas using Pydantic
- **Services Layer** (`app/services/`): Implements business logic and services
- **Utils Layer** (`app/utils/`): Contains utility functions and helpers

## Setup

1. Create a virtual environment and activate it:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Create a `.env` file based on `.env.example` and fill in your credentials:
   ```
   SUPABASE_URL=https://your-project-id.supabase.co
   SUPABASE_KEY=your-service-role-key
   GEMINI_API_KEY=your-gemini-api-key
   ```

4. Start the backend server:
   ```bash
   python -m main
   ```

## Database Schema

The application uses Supabase as the database. Below is the schema:

[
  {
    "table_name": "chatmessages",
    "column_name": "message_id",
    "data_type": "integer",
    "character_maximum_length": null,
    "is_nullable": "NO",
    "column_default": null,
    "constraint_type": "PRIMARY KEY",
    "referenced_table": "chatmessages",
    "referenced_column": "message_id"
  },
  {
    "table_name": "chatmessages",
    "column_name": "message_text",
    "data_type": "text",
    "character_maximum_length": null,
    "is_nullable": "NO",
    "column_default": null,
    "constraint_type": "",
    "referenced_table": null,
    "referenced_column": null
  },
  {
    "table_name": "chatmessages",
    "column_name": "project_id",
    "data_type": "integer",
    "character_maximum_length": null,
    "is_nullable": "NO",
    "column_default": null,
    "constraint_type": "",
    "referenced_table": null,
    "referenced_column": null
  },
  {
    "table_name": "chatmessages",
    "column_name": "sender_type",
    "data_type": "USER-DEFINED",
    "character_maximum_length": null,
    "is_nullable": "NO",
    "column_default": null,
    "constraint_type": "",
    "referenced_table": null,
    "referenced_column": null
  },
  {
    "table_name": "chatmessages",
    "column_name": "sent_at",
    "data_type": "timestamp without time zone",
    "character_maximum_length": null,
    "is_nullable": "YES",
    "column_default": "CURRENT_TIMESTAMP",
    "constraint_type": "",
    "referenced_table": null,
    "referenced_column": null
  },
  {
    "table_name": "chatmessages",
    "column_name": "user_id",
    "data_type": "uuid",
    "character_maximum_length": null,
    "is_nullable": "NO",
    "column_default": null,
    "constraint_type": "",
    "referenced_table": null,
    "referenced_column": null
  },
  {
    "table_name": "choices",
    "column_name": "choice_id",
    "data_type": "integer",
    "character_maximum_length": null,
    "is_nullable": "NO",
    "column_default": null,
    "constraint_type": "PRIMARY KEY",
    "referenced_table": "choices",
    "referenced_column": "choice_id"
  },
  {
    "table_name": "choices",
    "column_name": "choice_id",
    "data_type": "integer",
    "character_maximum_length": null,
    "is_nullable": "NO",
    "column_default": null,
    "constraint_type": "FOREIGN KEY",
    "referenced_table": "choices",
    "referenced_column": "choice_id"
  },
  {
    "table_name": "choices",
    "column_name": "choice_text",
    "data_type": "text",
    "character_maximum_length": null,
    "is_nullable": "NO",
    "column_default": null,
    "constraint_type": "",
    "referenced_table": null,
    "referenced_column": null
  },
  {
    "table_name": "choices",
    "column_name": "description",
    "data_type": "text",
    "character_maximum_length": null,
    "is_nullable": "YES",
    "column_default": null,
    "constraint_type": "",
    "referenced_table": null,
    "referenced_column": null
  },
  {
    "table_name": "choices",
    "column_name": "question_id",
    "data_type": "integer",
    "character_maximum_length": null,
    "is_nullable": "NO",
    "column_default": null,
    "constraint_type": "",
    "referenced_table": null,
    "referenced_column": null
  },
  {
    "table_name": "chunks",
    "column_name": "chunk_id",
    "data_type": "text",
    "character_maximum_length": null,
    "is_nullable": "NO",
    "column_default": null,
    "constraint_type": "",
    "referenced_table": null,
    "referenced_column": null
  },
  {
    "table_name": "chunks",
    "column_name": "contextualized_text",
    "data_type": "text",
    "character_maximum_length": null,
    "is_nullable": "YES",
    "column_default": null,
    "constraint_type": "",
    "referenced_table": null,
    "referenced_column": null
  },
  {
    "table_name": "chunks",
    "column_name": "embedding",
    "data_type": "USER-DEFINED",
    "character_maximum_length": null,
    "is_nullable": "YES",
    "column_default": null,
    "constraint_type": "",
    "referenced_table": null,
    "referenced_column": null
  },
  {
    "table_name": "chunks",
    "column_name": "id",
    "data_type": "integer",
    "character_maximum_length": null,
    "is_nullable": "NO",
    "column_default": "nextval('chunks_id_seq'::regclass)",
    "constraint_type": "PRIMARY KEY",
    "referenced_table": "chunks",
    "referenced_column": "id"
  },
  {
    "table_name": "chunks",
    "column_name": "metadata",
    "data_type": "jsonb",
    "character_maximum_length": null,
    "is_nullable": "YES",
    "column_default": null,
    "constraint_type": "",
    "referenced_table": null,
    "referenced_column": null
  },
  {
    "table_name": "chunks",
    "column_name": "raw_text",
    "data_type": "text",
    "character_maximum_length": null,
    "is_nullable": "YES",
    "column_default": null,
    "constraint_type": "",
    "referenced_table": null,
    "referenced_column": null
  },
  {
    "table_name": "pdfs",
    "column_name": "file_name",
    "data_type": "character varying",
    "character_maximum_length": 100,
    "is_nullable": "NO",
    "column_default": null,
    "constraint_type": "",
    "referenced_table": null,
    "referenced_column": null
  },
  {
    "table_name": "pdfs",
    "column_name": "file_path",
    "data_type": "character varying",
    "character_maximum_length": 255,
    "is_nullable": "NO",
    "column_default": null,
    "constraint_type": "",
    "referenced_table": null,
    "referenced_column": null
  },
  {
    "table_name": "pdfs",
    "column_name": "file_size",
    "data_type": "integer",
    "character_maximum_length": null,
    "is_nullable": "YES",
    "column_default": null,
    "constraint_type": "",
    "referenced_table": null,
    "referenced_column": null
  },
  {
    "table_name": "pdfs",
    "column_name": "pdf_id",
    "data_type": "integer",
    "character_maximum_length": null,
    "is_nullable": "NO",
    "column_default": null,
    "constraint_type": "PRIMARY KEY",
    "referenced_table": "pdfs",
    "referenced_column": "pdf_id"
  },
  {
    "table_name": "pdfs",
    "column_name": "project_id",
    "data_type": "integer",
    "character_maximum_length": null,
    "is_nullable": "NO",
    "column_default": null,
    "constraint_type": "",
    "referenced_table": null,
    "referenced_column": null
  },
  {
    "table_name": "pdfs",
    "column_name": "raw_text",
    "data_type": "text",
    "character_maximum_length": null,
    "is_nullable": "YES",
    "column_default": null,
    "constraint_type": "",
    "referenced_table": null,
    "referenced_column": null
  },
  {
    "table_name": "pdfs",
    "column_name": "upload_date",
    "data_type": "timestamp without time zone",
    "character_maximum_length": null,
    "is_nullable": "YES",
    "column_default": "CURRENT_TIMESTAMP",
    "constraint_type": "",
    "referenced_table": null,
    "referenced_column": null
  },
  {
    "table_name": "projects",
    "column_name": "created_at",
    "data_type": "timestamp without time zone",
    "character_maximum_length": null,
    "is_nullable": "YES",
    "column_default": "CURRENT_TIMESTAMP",
    "constraint_type": "",
    "referenced_table": null,
    "referenced_column": null
  },
  {
    "table_name": "projects",
    "column_name": "description",
    "data_type": "text",
    "character_maximum_length": null,
    "is_nullable": "YES",
    "column_default": null,
    "constraint_type": "",
    "referenced_table": null,
    "referenced_column": null
  },
  {
    "table_name": "projects",
    "column_name": "learning_objective",
    "data_type": "text",
    "character_maximum_length": null,
    "is_nullable": "YES",
    "column_default": null,
    "constraint_type": "",
    "referenced_table": null,
    "referenced_column": null
  },
  {
    "table_name": "projects",
    "column_name": "project_id",
    "data_type": "integer",
    "character_maximum_length": null,
    "is_nullable": "NO",
    "column_default": null,
    "constraint_type": "PRIMARY KEY",
    "referenced_table": "projects",
    "referenced_column": "project_id"
  },
  {
    "table_name": "projects",
    "column_name": "project_id",
    "data_type": "integer",
    "character_maximum_length": null,
    "is_nullable": "NO",
    "column_default": null,
    "constraint_type": "FOREIGN KEY",
    "referenced_table": "projects",
    "referenced_column": "project_id"
  },
  {
    "table_name": "projects",
    "column_name": "project_id",
    "data_type": "integer",
    "character_maximum_length": null,
    "is_nullable": "NO",
    "column_default": null,
    "constraint_type": "FOREIGN KEY",
    "referenced_table": "projects",
    "referenced_column": "project_id"
  },
  {
    "table_name": "projects",
    "column_name": "project_id",
    "data_type": "integer",
    "character_maximum_length": null,
    "is_nullable": "NO",
    "column_default": null,
    "constraint_type": "FOREIGN KEY",
    "referenced_table": "projects",
    "referenced_column": "project_id"
  },
  {
    "table_name": "projects",
    "column_name": "project_name",
    "data_type": "character varying",
    "character_maximum_length": 100,
    "is_nullable": "NO",
    "column_default": null,
    "constraint_type": "",
    "referenced_table": null,
    "referenced_column": null
  },
  {
    "table_name": "projects",
    "column_name": "research_type",
    "data_type": "USER-DEFINED",
    "character_maximum_length": null,
    "is_nullable": "YES",
    "column_default": null,
    "constraint_type": "",
    "referenced_table": null,
    "referenced_column": null
  },
  {
    "table_name": "projects",
    "column_name": "user_id",
    "data_type": "uuid",
    "character_maximum_length": null,
    "is_nullable": "NO",
    "column_default": null,
    "constraint_type": "",
    "referenced_table": null,
    "referenced_column": null
  },
  {
    "table_name": "questions",
    "column_name": "question_id",
    "data_type": "integer",
    "character_maximum_length": null,
    "is_nullable": "NO",
    "column_default": null,
    "constraint_type": "FOREIGN KEY",
    "referenced_table": "questions",
    "referenced_column": "question_id"
  },
  {
    "table_name": "questions",
    "column_name": "question_id",
    "data_type": "integer",
    "character_maximum_length": null,
    "is_nullable": "NO",
    "column_default": null,
    "constraint_type": "PRIMARY KEY",
    "referenced_table": "questions",
    "referenced_column": "question_id"
  },
  {
    "table_name": "questions",
    "column_name": "question_id",
    "data_type": "integer",
    "character_maximum_length": null,
    "is_nullable": "NO",
    "column_default": null,
    "constraint_type": "FOREIGN KEY",
    "referenced_table": "questions",
    "referenced_column": "question_id"
  },
  {
    "table_name": "questions",
    "column_name": "question_text",
    "data_type": "text",
    "character_maximum_length": null,
    "is_nullable": "NO",
    "column_default": null,
    "constraint_type": "",
    "referenced_table": null,
    "referenced_column": null
  },
  {
    "table_name": "sources",
    "column_name": "chunk_id",
    "data_type": "text",
    "character_maximum_length": null,
    "is_nullable": "NO",
    "column_default": null,
    "constraint_type": "",
    "referenced_table": "sources",
    "referenced_column": "chunk_id"
  },
  {
    "table_name": "sources",
    "column_name": "created_at",
    "data_type": "timestamp with time zone",
    "character_maximum_length": null,
    "is_nullable": "YES",
    "column_default": "now()",
    "constraint_type": "",
    "referenced_table": null,
    "referenced_column": null
  },
  {
    "table_name": "sources",
    "column_name": "embedding",
    "data_type": "USER-DEFINED",
    "character_maximum_length": null,
    "is_nullable": "YES",
    "column_default": null,
    "constraint_type": "",
    "referenced_table": null,
    "referenced_column": null
  },
  {
    "table_name": "sources",
    "column_name": "id",
    "data_type": "integer",
    "character_maximum_length": null,
    "is_nullable": "NO",
    "column_default": "nextval('sources_id_seq'::regclass)",
    "constraint_type": "PRIMARY KEY",
    "referenced_table": "sources",
    "referenced_column": "id"
  },
  {
    "table_name": "sources",
    "column_name": "metadata",
    "data_type": "jsonb",
    "character_maximum_length": null,
    "is_nullable": "YES",
    "column_default": null,
    "constraint_type": "",
    "referenced_table": null,
    "referenced_column": null
  },
  {
    "table_name": "sources",
    "column_name": "raw_text",
    "data_type": "text",
    "character_maximum_length": null,
    "is_nullable": "YES",
    "column_default": null,
    "constraint_type": "",
    "referenced_table": null,
    "referenced_column": null
  },
  {
    "table_name": "sources",
    "column_name": "source_id",
    "data_type": "text",
    "character_maximum_length": null,
    "is_nullable": "NO",
    "column_default": null,
    "constraint_type": "",
    "referenced_table": null,
    "referenced_column": null
  },
  {
    "table_name": "userresponses",
    "column_name": "choice_id",
    "data_type": "integer",
    "character_maximum_length": null,
    "is_nullable": "NO",
    "column_default": null,
    "constraint_type": "",
    "referenced_table": null,
    "referenced_column": null
  },
  {
    "table_name": "userresponses",
    "column_name": "project_id",
    "data_type": "integer",
    "character_maximum_length": null,
    "is_nullable": "NO",
    "column_default": null,
    "constraint_type": "",
    "referenced_table": "userresponses",
    "referenced_column": "project_id"
  },
  {
    "table_name": "userresponses",
    "column_name": "question_id",
    "data_type": "integer",
    "character_maximum_length": null,
    "is_nullable": "NO",
    "column_default": null,
    "constraint_type": "",
    "referenced_table": "userresponses",
    "referenced_column": "question_id"
  },
  {
    "table_name": "userresponses",
    "column_name": "response_id",
    "data_type": "integer",
    "character_maximum_length": null,
    "is_nullable": "NO",
    "column_default": null,
    "constraint_type": "PRIMARY KEY",
    "referenced_table": "userresponses",
    "referenced_column": "response_id"
  },
  {
    "table_name": "userresponses",
    "column_name": "user_id",
    "data_type": "uuid",
    "character_maximum_length": null,
    "is_nullable": "NO",
    "column_default": null,
    "constraint_type": "",
    "referenced_table": null,
    "referenced_column": null
  }
]
## API Endpoints

- `POST /query`: Query the research assistant with a specific question
- `POST /chat`: Chat with the research assistant, maintaining conversation history
- `POST /upload`: Upload a PDF file for analysis and storage
- `GET /health`: Health check endpoint

## Development

### Adding New Features

1. Define new models in `app/models/schemas.py`
2. Implement business logic in `app/services/`
3. Add new API endpoints in `app/api/routes.py`
4. Update configuration if needed in `app/core/config.py`

### Error Handling

The application uses a centralized error handling system:

- `app/utils/error_handlers.py` contains exception handlers
- Use the `AppException` class for application-specific exceptions

### Logging

Logging is configured in `app/core/config.py` and uses both the standard Python logging module and Loguru for enhanced logging capabilities.

## Testing

To run tests:

```bash
pytest
```

## Deployment

The application can be deployed using Docker:

```bash
docker build -t research-assistant-backend .
docker run -p 8000:8000 research-assistant-backend
```

## PDF Ingestion Pipeline

The application includes a comprehensive PDF ingestion pipeline that processes research papers and makes them available for semantic search:

1. **PDF Parsing**: Extracts text and tables from PDF files
2. **Content Chunking**: Splits the content into manageable chunks based on semantic boundaries
3. **Embedding Generation**: Creates vector embeddings for each chunk
4. **Database Storage**: Stores chunks and embeddings in Supabase for retrieval

### Using the Ingestion Pipeline

#### Via API Endpoints

- `POST /ingest`: Upload and process a single PDF file
- `POST /batch-ingest`: Upload and process multiple PDF files

#### Via Command-Line Scripts

The `scripts` directory contains command-line tools for PDF ingestion:

```bash
# Single PDF ingestion
python scripts/ingest_pdf.py --pdf_path /path/to/your/file.pdf [--project_id 123]

# Batch PDF ingestion
python scripts/batch_ingest_pdfs.py --pdf_dir /path/to/pdf/directory [--project_id 123]
```

See the [scripts README](scripts/README.md) for more details. 