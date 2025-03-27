-- Fix for match_sources_by_project function
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
    sources.id::bigint,  -- Explicitly cast to bigint to fix type mismatch
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

-- Fix for match_sources function
CREATE OR REPLACE FUNCTION match_sources(
  query_embedding vector(1536),
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
    sources.id::bigint,  -- Explicitly cast to bigint to fix type mismatch
    sources.source_id,
    sources.chunk_id,
    sources.raw_text,  -- Using raw_text instead of contextualized_text
    sources.metadata,
    1 - (sources.embedding <=> query_embedding) as similarity
  FROM sources
  WHERE 
    1 - (sources.embedding <=> query_embedding) > match_threshold
  ORDER BY similarity DESC
  LIMIT match_count;
END;
$$; 