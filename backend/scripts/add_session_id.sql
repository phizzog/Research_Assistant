-- Add session_id column to chathistory table
ALTER TABLE chathistory ADD COLUMN session_id UUID;

-- Create an index on session_id for faster lookups
CREATE INDEX idx_chathistory_session_id ON chathistory(session_id);

-- Set default session_id for existing messages (using a random UUID for each group)
WITH message_groups AS (
  SELECT DISTINCT project_id, user_id, DATE(sent_at) as message_date
  FROM chathistory
)
UPDATE chathistory ch
SET session_id = gen_random_uuid()
FROM message_groups mg
WHERE ch.project_id = mg.project_id 
  AND ch.user_id = mg.user_id 
  AND DATE(ch.sent_at) = mg.message_date
  AND ch.session_id IS NULL; 