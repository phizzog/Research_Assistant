-- Create a function to match chunks from the book
CREATE OR REPLACE FUNCTION match_book_chunks(
  query_embedding vector(1536),
  match_count int DEFAULT 5,
  match_threshold float DEFAULT 0.5
) RETURNS TABLE (
  id bigint,
  content text,
  metadata jsonb,
  similarity float
)
LANGUAGE plpgsql
AS $$
BEGIN
  RETURN QUERY
  SELECT
    chunks.id::bigint,
    chunks.raw_text as content,
    chunks.metadata,
    1 - (chunks.embedding <=> query_embedding) as similarity
  FROM chunks
  WHERE 
    1 - (chunks.embedding <=> query_embedding) > match_threshold
  ORDER BY similarity DESC
  LIMIT match_count;
END;
$$; 