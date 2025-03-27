import requests
import tempfile
import os
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter

def create_test_pdf(output_path):
    """Create a simple PDF file for testing"""
    c = canvas.Canvas(output_path, pagesize=letter)
    c.drawString(100, 750, "Test PDF Document")
    c.drawString(100, 700, "This is a simple PDF file created for testing the /ingest endpoint.")
    c.drawString(100, 650, "It contains some text that should be processed by the PDF ingestion pipeline.")
    c.drawString(100, 600, "Testing with simple_mode=true parameter.")
    c.save()
    print(f"Created test PDF at {output_path}")

def test_ingest_endpoint(pdf_path, project_id=None):
    """Test the /ingest endpoint with a PDF file"""
    # API endpoint
    url = "http://localhost:8000/ingest"
    
    # Prepare form data
    form_data = {'simple_mode': 'true'}
    if project_id:
        form_data['project_id'] = str(project_id)
    
    # Prepare file
    files = {'file': ('test.pdf', open(pdf_path, 'rb'), 'application/pdf')}
    
    # Send request
    print(f"Sending request to {url} with simple_mode=true")
    try:
        response = requests.post(url, data=form_data, files=files)
        
        # Check response
        if response.status_code == 200:
            print("Request successful!")
            print(f"Response: {response.json()}")
            return True
        else:
            print(f"Request failed with status code: {response.status_code}")
            print(f"Response: {response.text}")
            return False
    except Exception as e:
        print(f"Error: {str(e)}")
        return False
    finally:
        # Close file
        files['file'][1].close()

if __name__ == "__main__":
    # Create a temporary directory for the test PDF
    with tempfile.TemporaryDirectory() as temp_dir:
        pdf_path = os.path.join(temp_dir, "test.pdf")
        
        # Create test PDF
        create_test_pdf(pdf_path)
        
        # Test endpoint
        test_ingest_endpoint(pdf_path) 