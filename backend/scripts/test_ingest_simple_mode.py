#!/usr/bin/env python3
"""
Script to test the /ingest endpoint with simple_mode=True parameter to ensure it 
works correctly.
"""
import argparse
import json
import logging
import os
import sys
import time
from pathlib import Path
import requests
from rich.console import Console
from rich.logging import RichHandler

# Configure logging
FORMAT = "%(message)s"
logging.basicConfig(
    level=logging.INFO,
    format=FORMAT,
    datefmt="[%X]",
    handlers=[RichHandler(rich_tracebacks=True)]
)
logger = logging.getLogger("rich")
console = Console()

def test_ingest_simple_mode(pdf_path, project_id=None, api_url="http://localhost:8000"):
    """
    Test the /ingest endpoint with simple_mode=True
    
    Args:
        pdf_path: Path to the PDF file to test with
        project_id: Optional project ID to use for the test
        api_url: Base URL for the API
    
    Returns:
        True if the test was successful, False otherwise
    """
    logger.info(f"Testing /ingest endpoint with simple_mode=True for file: {pdf_path}")
    
    # Ensure the file exists
    if not os.path.exists(pdf_path):
        logger.error(f"File not found: {pdf_path}")
        return False
    
    # Create the request
    url = f"{api_url}/ingest"
    
    files = {'file': open(pdf_path, 'rb')}
    data = {'simple_mode': 'true'}
    
    if project_id is not None:
        data['project_id'] = str(project_id)
        logger.info(f"Using project_id: {project_id}")
    
    try:
        # Make the request
        logger.info(f"Sending request to {url}")
        response = requests.post(url, files=files, data=data)
        
        # Check the response
        if response.status_code == 200:
            response_data = response.json()
            logger.info(f"Response: {json.dumps(response_data, indent=2)}")
            logger.info("✅ Test successful!")
            
            # Check if the response contains expected fields
            if "answer" in response_data:
                logger.info("✅ Response contains 'answer' field as expected for simple_mode=True")
            else:
                logger.warning("⚠️ Response does not contain 'answer' field, which is expected for simple_mode=True")
            
            return True
        else:
            logger.error(f"❌ Request failed with status code: {response.status_code}")
            logger.error(f"Response: {response.text}")
            return False
    except Exception as e:
        logger.error(f"❌ Exception occurred: {e}")
        return False
    finally:
        # Close the file
        files['file'].close()

def main():
    parser = argparse.ArgumentParser(description='Test the /ingest endpoint with simple_mode=True')
    parser.add_argument('--pdf', type=str, required=True, help='Path to the PDF file to test with')
    parser.add_argument('--project-id', type=int, required=False, help='Project ID to use for the test')
    parser.add_argument('--api-url', type=str, default='http://localhost:8000', help='Base URL for the API')
    
    args = parser.parse_args()
    
    success = test_ingest_simple_mode(args.pdf, args.project_id, args.api_url)
    
    if success:
        logger.info("✅ All tests passed!")
        return 0
    else:
        logger.error("❌ Tests failed!")
        return 1

if __name__ == '__main__':
    sys.exit(main()) 