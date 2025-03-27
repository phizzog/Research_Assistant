-- Drop all existing match_sources functions with different parameter combinations
DROP FUNCTION IF EXISTS match_sources(vector, integer);
DROP FUNCTION IF EXISTS match_sources(vector, integer, double precision);
DROP FUNCTION IF EXISTS match_sources(query_embedding vector, match_count integer);
DROP FUNCTION IF EXISTS match_sources(query_embedding vector, match_count integer, match_threshold double precision);

-- Now create a single match_sources function with a distinct name to avoid conflicts
CREATE OR REPLACE FUNCTION match_sources_v2(
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
    sources.id::bigint,
    sources.source_id,
    sources.chunk_id,
    sources.raw_text,
    sources.metadata,
    1 - (sources.embedding <=> query_embedding) as similarity
  FROM sources
  WHERE 
    1 - (sources.embedding <=> query_embedding) > match_threshold
  ORDER BY similarity DESC
  LIMIT match_count;
END;
$$; 