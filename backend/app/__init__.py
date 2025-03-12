from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from app.api.routes import router
from app.core.config import CORS_ORIGINS, API_HOST, API_PORT, logger
from app.utils.error_handlers import validation_exception_handler, AppException, app_exception_handler

def create_app() -> FastAPI:
    """Create and configure the FastAPI application"""
    app = FastAPI(title="Research Assistant API")
    
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Add exception handlers
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(AppException, app_exception_handler)
    
    # Include API routes
    app.include_router(router)
    
    # Add startup event handler
    @app.on_event("startup")
    async def startup_event():
        logger.info("Starting Research Assistant API")
    
    # Add shutdown event handler
    @app.on_event("shutdown")
    async def shutdown_event():
        logger.info("Shutting down Research Assistant API")
    
    return app
