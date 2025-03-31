# Supabase Database Functions

This directory contains PostgreSQL functions for the Research Assistant application.

## Deploying Functions

### Function: `delete_source_complete`

This function handles the complete deletion of a source, including:
1. Removing the source from a project's sources array
2. Deleting all source chunks from the sources table

#### How to Deploy

1. **Log in to Supabase**
   - Access your Supabase project dashboard
   - Go to "SQL Editor"

2. **Create a New Query**
   - Click "New Query"
   - Copy the entire contents of `delete_source_complete.sql` into the editor

3. **Run the Query**
   - Click "Run" to create the function in your database

4. **Test the Function**
   - You can test the function with a query like:
   ```sql
   SELECT * FROM delete_source_complete('your_document_id', your_project_id);
   ```

#### How It Works

The function expects two parameters:
- `doc_id`: The document_id of the source to delete
- `proj_id`: The project_id from which to remove the source

It returns a boolean indicating success or failure.

#### Notes

- The function is declared with `SECURITY DEFINER`, which means it runs with the permissions of the user who created it
- Error handling is included to gracefully handle cases where the source or project doesn't exist
- If the sources array becomes empty, it's set to an empty array rather than NULL 