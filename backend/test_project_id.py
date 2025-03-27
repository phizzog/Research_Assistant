#!/usr/bin/env python
"""
Test script to verify project_id is correctly stored in the sources table
"""
import os
import sys
import json
import logging
import random
import numpy as np
from typing import List

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Import Supabase directly from environment
import os
from dotenv import load_dotenv
load_dotenv()

from supabase import create_client, Client

# Create Supabase client directly
url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")
supabase = create_client(url, key)

def mock_embedding(text: str) -> List[float]:
    """Create a mock embedding for testing"""
    # Generate a random 1536-dimensional vector for testing
    np.random.seed(hash(text) % 2**32)
    return np.random.normal(0, 1, 1536).tolist()

def test_project_id_insertion():
    """Test that project_id is correctly inserted at the root level"""
    
    # Create a test record with project_id
    test_record = {
        "source_id": "test_source_id",
        "chunk_id": f"test_chunk_id_{random.randint(10000, 99999)}",  # Generate unique ID
        "raw_text": "This is a test record to verify project_id storage",
        "embedding": mock_embedding("This is a test record"),
        "metadata": {
            "source": "test.pdf",
            "document_id": "test_doc_id",
            "project_id": 999  # Also set in metadata
        },
        "project_id": 999  # Set at root level
    }
    
    logger.info(f"Inserting test record with project_id={test_record['project_id']}")
    logger.info(f"Test record chunk_id: {test_record['chunk_id']}")
    
    # Insert using our new approach with explicit project_id
    response = supabase.table("sources").upsert(
        test_record,
        on_conflict="chunk_id",
        returning="representation"  # Return the full record
    ).execute()
    
    # Check results
    if response.data:
        logger.info(f"Successfully inserted test record")
        
        # Verify project_id is correctly stored
        inserted_project_id = response.data[0].get("project_id")
        logger.info(f"Inserted project_id: {inserted_project_id}")
        
        if inserted_project_id == 999:
            logger.info("SUCCESS: project_id correctly stored at root level!")
        else:
            logger.error(f"FAILURE: project_id not correctly stored. Got {inserted_project_id}, expected 999")
    else:
        logger.error(f"Failed to insert test record: {response.error}")

    # Now query to double check
    query_response = supabase.table("sources").select("*").eq("chunk_id", test_record["chunk_id"]).execute()
    
    if query_response.data:
        queried_project_id = query_response.data[0].get("project_id")
        logger.info(f"Queried project_id: {queried_project_id}")
        
        if queried_project_id == 999:
            logger.info("SUCCESS: project_id correctly queried from root level!")
        else:
            logger.error(f"FAILURE: project_id not correctly queried. Got {queried_project_id}, expected 999")
    else:
        logger.error(f"Failed to query test record")

if __name__ == "__main__":
    test_project_id_insertion() 