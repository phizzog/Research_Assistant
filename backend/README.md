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

| table_name    | column_name         | data_type                   | character_maximum_length | is_nullable | column_default                     | constraint_type | referenced_table | referenced_column |
| ------------- | ------------------- | --------------------------- | ------------------------ | ----------- | ---------------------------------- | --------------- | ---------------- | ----------------- |
| chatmessages  | message_id          | integer                     | null                     | NO          | null                               | PRIMARY KEY     | chatmessages     | message_id        |
| chatmessages  | message_text        | text                        | null                     | NO          | null                               |                 | null             | null              |
| chatmessages  | project_id          | integer                     | null                     | NO          | null                               |                 | null             | null              |
| chatmessages  | sender_type         | USER-DEFINED                | null                     | NO          | null                               |                 | null             | null              |
| chatmessages  | sent_at             | timestamp without time zone | null                     | YES         | CURRENT_TIMESTAMP                  |                 | null             | null              |
| chatmessages  | user_id             | uuid                        | null                     | NO          | null                               |                 | null             | null              |
| choices       | choice_id           | integer                     | null                     | NO          | null                               | FOREIGN KEY     | choices          | choice_id         |
| choices       | choice_id           | integer                     | null                     | NO          | null                               | PRIMARY KEY     | choices          | choice_id         |
| choices       | choice_text         | text                        | null                     | NO          | null                               |                 | null             | null              |
| choices       | description         | text                        | null                     | YES         | null                               |                 | null             | null              |
| choices       | question_id         | integer                     | null                     | NO          | null                               |                 | null             | null              |
| chunks        | chunk_id            | text                        | null                     | NO          | null                               |                 | null             | null              |
| chunks        | contextualized_text | text                        | null                     | YES         | null                               |                 | null             | null              |
| chunks        | embedding           | USER-DEFINED                | null                     | YES         | null                               |                 | null             | null              |
| chunks        | id                  | integer                     | null                     | NO          | nextval('chunks_id_seq'::regclass) | PRIMARY KEY     | chunks           | id                |
| chunks        | metadata            | jsonb                       | null                     | YES         | null                               |                 | null             | null              |
| chunks        | raw_text            | text                        | null                     | YES         | null                               |                 | null             | null              |
| pdfs          | file_name           | character varying           | 100                      | NO          | null                               |                 | null             | null              |
| pdfs          | file_path           | character varying           | 255                      | NO          | null                               |                 | null             | null              |
| pdfs          | file_size           | integer                     | null                     | YES         | null                               |                 | null             | null              |
| pdfs          | pdf_id              | integer                     | null                     | NO          | null                               | PRIMARY KEY     | pdfs             | pdf_id            |
| pdfs          | project_id          | integer                     | null                     | NO          | null                               |                 | null             | null              |
| pdfs          | raw_text            | text                        | null                     | YES         | null                               |                 | null             | null              |
| pdfs          | upload_date         | timestamp without time zone | null                     | YES         | CURRENT_TIMESTAMP                  |                 | null             | null              |
| projects      | created_at          | timestamp without time zone | null                     | YES         | CURRENT_TIMESTAMP                  |                 | null             | null              |
| projects      | description         | text                        | null                     | YES         | null                               |                 | null             | null              |
| projects      | learning_objective  | text                        | null                     | YES         | null                               |                 | null             | null              |
| projects      | project_id          | integer                     | null                     | NO          | null                               | FOREIGN KEY     | projects         | project_id        |
| projects      | project_id          | integer                     | null                     | NO          | null                               | PRIMARY KEY     | projects         | project_id        |
| projects      | project_id          | integer                     | null                     | NO          | null                               | FOREIGN KEY     | projects         | project_id        |
| projects      | project_id          | integer                     | null                     | NO          | null                               | FOREIGN KEY     | projects         | project_id        |
| projects      | project_name        | character varying           | 100                      | NO          | null                               |                 | null             | null              |
| projects      | research_type       | USER-DEFINED                | null                     | YES         | null                               |                 | null             | null              |
| projects      | user_id             | uuid                        | null                     | NO          | null                               |                 | null             | null              |
| questions     | question_id         | integer                     | null                     | NO          | null                               | PRIMARY KEY     | questions        | question_id       |
| questions     | question_id         | integer                     | null                     | NO          | null                               | FOREIGN KEY     | questions        | question_id       |
| questions     | question_id         | integer                     | null                     | NO          | null                               | FOREIGN KEY     | questions        | question_id       |
| questions     | question_text       | text                        | null                     | NO          | null                               |                 | null             | null              |
| userresponses | choice_id           | integer                     | null                     | NO          | null                               |                 | null             | null              |
| userresponses | project_id          | integer                     | null                     | NO          | null                               |                 | userresponses    | project_id        |
| userresponses | question_id         | integer                     | null                     | NO          | null                               |                 | userresponses    | question_id       |
| userresponses | response_id         | integer                     | null                     | NO          | null                               | PRIMARY KEY     | userresponses    | response_id       |
| userresponses | user_id             | uuid                        | null                     | NO          | null                               |                 | null             | null              |

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