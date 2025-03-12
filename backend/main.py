import uvicorn
from app import create_app
from app.core.config import API_HOST, API_PORT, logger

# Create the FastAPI application
app = create_app()

if __name__ == "__main__":
    logger.info(f"Starting server on {API_HOST}:{API_PORT}")
    uvicorn.run(app, host=API_HOST, port=API_PORT) 