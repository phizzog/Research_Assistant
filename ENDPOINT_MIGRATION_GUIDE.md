# API Endpoint Migration Guide

## Overview

The `/upload` endpoint has been **completely removed** from the Research Assistant API. All file upload functionality is now handled by the `/ingest` endpoint, which provides more flexibility and better project integration.

## Migration Complete

This migration is now complete. The `/upload` endpoint is no longer available in the system. All clients must use the `/ingest` endpoint with the appropriate parameters.

## Background

Previously, the system had two separate endpoints for handling file uploads:

1. `/upload` - A simple endpoint for uploading and processing PDF files
2. `/ingest` - A more advanced endpoint with additional features

This caused confusion and duplicated functionality. The `/ingest` endpoint now handles all file upload scenarios with the `simple_mode` parameter to support basic use cases.

## Migration Options

If you were previously using the `/upload` endpoint, you must update your code to use one of these options:

### Option 1: Use `/ingest` with `simple_mode=true`

This is the simplest migration path and provides behavior most similar to the old `/upload` endpoint:

```diff
- POST /upload
+ POST /ingest
+ Body: FormData with 'simple_mode' set to true
```

Example:
```javascript
const formData = new FormData();
formData.append('file', fileObject);
formData.append('simple_mode', 'true');
if (projectId) {
  formData.append('project_id', projectId.toString());
}

// Use the /ingest endpoint instead of /upload
const response = await fetch(`${API_BASE_URL}/ingest`, {
  method: 'POST',
  body: formData,
});
```

### Option 2: Use the full `/ingest` capabilities

If you want to leverage the advanced features of the `/ingest` endpoint:

```diff
- POST /upload
+ POST /ingest
+ Body: FormData with additional parameters
```

Example:
```javascript
const formData = new FormData();
formData.append('file', fileObject);
formData.append('project_id', projectId.toString());
formData.append('user_id', userId);
formData.append('process_type', 'full');

const response = await fetch(`${API_BASE_URL}/ingest`, {
  method: 'POST',
  body: formData,
});
```

## Response Format Differences

When using `simple_mode=true`:
- The response will match the old `/upload` endpoint format
- You'll receive a user-friendly message in the `answer` field

When using the full `/ingest` capabilities:
- You'll receive detailed processing statistics
- For projects, source information will be included

## Need Help?

If you encounter any issues with the migration, please contact the development team. 