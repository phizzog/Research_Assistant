# Debugging & Fixing NULL Project IDs in Sources Table

This guide will help diagnose and fix the issue with sources being uploaded without project_id values.

## Diagnosis

### 1. Check Current State

Run the verification script to check the current state of project_id in the sources table:

```bash
cd backend
python scripts/verify_sources_project_id.py
```

This will show:
- Total number of sources
- Number of sources with project_id set
- Number of sources without project_id (NULL)
- Any inconsistencies where chunks from the same source have different project_id values

### 2. Test a New Upload

To test if the fixes are working, upload a new PDF with a specific project_id:

```bash
cd backend
python scripts/test_pdf_upload.py /path/to/your/pdf/file.pdf 123  # Replace 123 with your project ID
```

This will:
1. Upload the PDF and associate it with the specified project_id
2. Verify if all sources created have the correct project_id
3. Log detailed information about the process

## Fixing NULL Project IDs

### Option 1: Update Existing Sources

If you have sources with NULL project_id that should be associated with a specific project, you can update them using the verification script:

```bash
cd backend
python scripts/verify_sources_project_id.py --update 123  # Replace 123 with your project ID
```

This will update ALL sources with NULL project_id to the specified project_id.

To update only sources from a specific document, first find the source_id pattern:

```bash
cd backend
python scripts/verify_sources_project_id.py
```

Then use the source_id to update only those sources:

```bash
cd backend
python scripts/verify_sources_project_id.py --update 123 --source_id "source_document123_1234567890"
```

### Option 2: Restart Upload Process

If you prefer to re-upload the PDFs with the correct project_id:

1. Delete the sources with NULL project_id (be careful!)
2. Re-upload the PDFs with the correct project_id using the `/ingest` endpoint

## Prevention

The code fixes made should prevent this issue from happening again:

1. The `store_pdf_content` function now properly logs and passes the project_id
2. The PDFEmbedder class now correctly processes the project_id parameter
3. The `/upload` endpoint now accepts and processes the project_id parameter
4. Added extensive logging to track project_id throughout the upload process

## Verification

After fixing existing sources or re-uploading PDFs, run the verification script again to confirm the changes:

```bash
cd backend
python scripts/verify_sources_project_id.py
```

All sources should now have the appropriate project_id values. 