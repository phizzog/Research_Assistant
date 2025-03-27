-- Function to update project sources when a new source is inserted
CREATE OR REPLACE FUNCTION update_project_sources()
RETURNS TRIGGER AS $$
DECLARE
    doc_id TEXT;
    doc_exists BOOLEAN;
    source_info JSONB;
BEGIN
    -- Extract document_id from metadata
    IF NEW.metadata IS NOT NULL AND NEW.metadata ? 'document_id' THEN
        doc_id := NEW.metadata->>'document_id';
        
        -- Check if this document already exists in the project's sources
        SELECT EXISTS (
            SELECT 1 
            FROM projects 
            WHERE project_id = NEW.project_id 
            AND sources @> ANY (ARRAY[jsonb_build_array(jsonb_build_object('document_id', doc_id))])
        ) INTO doc_exists;
        
        -- If document doesn't exist in sources, add it
        IF NOT doc_exists AND doc_id IS NOT NULL THEN
            -- Create the source info object
            source_info := jsonb_build_object(
                'document_id', doc_id,
                'source_id', NEW.source_id,
                'added_at', CURRENT_TIMESTAMP
            );
            
            -- Add any additional metadata we want to include
            IF NEW.metadata ? 'document_title' AND (NEW.metadata->>'document_title') <> '' THEN
                source_info := source_info || jsonb_build_object('title', NEW.metadata->>'document_title');
            ELSE
                -- Use document_id as title if no title is available
                source_info := source_info || jsonb_build_object('title', doc_id);
            END IF;
            
            -- Update the projects table by appending to the sources array
            UPDATE projects
            SET sources = sources || jsonb_build_array(source_info)
            WHERE project_id = NEW.project_id;
        END IF;
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to run the function after each row is inserted into sources
CREATE OR REPLACE TRIGGER after_source_insert
AFTER INSERT ON sources
FOR EACH ROW
EXECUTE FUNCTION update_project_sources();

-- Optional: Also update on source update (if metadata or project_id might change)
CREATE OR REPLACE TRIGGER after_source_update
AFTER UPDATE OF metadata, project_id ON sources
FOR EACH ROW
WHEN (OLD.metadata->>'document_id' IS DISTINCT FROM NEW.metadata->>'document_id' OR OLD.project_id IS DISTINCT FROM NEW.project_id)
EXECUTE FUNCTION update_project_sources(); 