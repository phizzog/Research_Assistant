-- Function to completely delete a source and all related data
-- Parameters:
--   doc_id: The document_id of the source to delete
--   proj_id: The project_id from which to remove the source
CREATE OR REPLACE FUNCTION public.delete_source_complete(doc_id TEXT, proj_id INT)
RETURNS BOOLEAN
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
  updated_sources JSONB;
  source_count INT;
BEGIN
  -- Check if the source exists in the sources table
  SELECT COUNT(*) INTO source_count
  FROM sources
  WHERE document_id = doc_id;
  
  IF source_count = 0 THEN
    RAISE EXCEPTION 'Source with document_id % not found', doc_id;
  END IF;
  
  -- 1. Get current sources array from project
  SELECT sources INTO updated_sources
  FROM projects
  WHERE project_id = proj_id;
  
  IF updated_sources IS NULL THEN
    RAISE EXCEPTION 'Project with ID % not found or has no sources', proj_id;
  END IF;
  
  -- 2. Filter out the source to be deleted
  updated_sources := (
    SELECT jsonb_agg(source)
    FROM jsonb_array_elements(updated_sources) AS source
    WHERE (source->>'document_id') != doc_id
  );
  
  -- Handle case where the array becomes empty
  IF updated_sources IS NULL THEN
    updated_sources := '[]'::jsonb;
  END IF;
  
  -- 3. Update the project with the filtered sources
  UPDATE projects
  SET sources = updated_sources
  WHERE project_id = proj_id;
  
  -- 4. Delete all associated data from the sources table
  DELETE FROM sources
  WHERE document_id = doc_id;
  
  -- 5. Return success
  RETURN TRUE;
  
EXCEPTION WHEN OTHERS THEN
  -- Log the error
  RAISE NOTICE 'Error deleting source: %', SQLERRM;
  RETURN FALSE;
END;
$$; 