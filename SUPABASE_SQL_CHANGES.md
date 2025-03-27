# Linking Sources to Projects in Supabase

This guide outlines the necessary changes to link sources to projects in your Research Assistant application.

## Database Schema Changes

1. **Add Project ID Column to Sources Table**

Run the following SQL in the Supabase SQL Editor:

```sql
-- Add project_id column to sources table
ALTER TABLE sources 
ADD COLUMN project_id INTEGER NULL;

-- Add foreign key constraint (optional)
ALTER TABLE sources
ADD CONSTRAINT fk_sources_project
FOREIGN KEY (project_id)
REFERENCES projects(project_id)
ON DELETE CASCADE;

-- Add index for faster queries (recommended)
CREATE INDEX idx_sources_project_id ON sources(project_id);
```

2. **Create SQL Function for Project-Specific Source Matching**

Create a new SQL function to match sources by project:

```sql
CREATE OR REPLACE FUNCTION match_sources_by_project(
  query_embedding vector(1536),
  p_project_id integer,
  match_count int DEFAULT 5,
  match_threshold float DEFAULT 0.5
) RETURNS TABLE (
  id bigint,
  source_id text,
  chunk_id text,
  raw_text text,
  metadata jsonb,
  similarity float
)
LANGUAGE plpgsql
AS $$
BEGIN
  RETURN QUERY
  SELECT
    sources.id,
    sources.source_id,
    sources.chunk_id,
    sources.raw_text,
    sources.metadata,
    1 - (sources.embedding <=> query_embedding) as similarity
  FROM sources
  WHERE 
    project_id = p_project_id AND
    1 - (sources.embedding <=> query_embedding) > match_threshold
  ORDER BY similarity DESC
  LIMIT match_count;
END;
$$;
```

## Data Migration (Optional)

If you have existing sources that need to be linked to projects, you can run a migration script:

```sql
-- Example: Link sources to projects based on source_id patterns or other criteria
UPDATE sources 
SET project_id = 123  -- Replace with actual project ID
WHERE source_id LIKE 'source_document123_%';
```

## Testing the Implementation

After making these changes:

1. Upload a new PDF to a specific project using the `/ingest` endpoint with a `project_id`
2. Query the data using the `/query` endpoint with the same `project_id`
3. Verify that only sources from that project are returned in the results

## Using the Project-Specific Query

When making API calls to query the data, include the `project_id` parameter to restrict results to a specific project:

```json
{
  "query": "Your search query",
  "top_k": 5,
  "project_id": 123
}
```

## Benefits of This Approach

- **Better Organization:** Sources are directly linked to their respective projects
- **Improved Search Relevance:** Queries are scoped to project-specific context
- **Efficient Queries:** Database-level filtering improves performance
- **Clean Data Management:** Proper relational database design for easier maintenance 