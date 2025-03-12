"""Error handling utilities for the application."""
from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from app.core.config import logger

async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """
    Handle validation errors and return a user-friendly response.
    
    Args:
        request: The request that caused the exception
        exc: The validation exception
        
    Returns:
        JSONResponse: A formatted error response
    """
    logger.error(f"Validation error: {exc}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": "Validation Error",
            "detail": exc.errors(),
            "message": "Please check your request parameters and try again."
        }
    )

class AppException(Exception):
    """
    Base exception class for application-specific exceptions.
    
    Attributes:
        message: The error message
        status_code: The HTTP status code to return
    """
    def __init__(self, message: str, status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)

async def app_exception_handler(request: Request, exc: AppException):
    """
    Handle application-specific exceptions.
    
    Args:
        request: The request that caused the exception
        exc: The application exception
        
    Returns:
        JSONResponse: A formatted error response
    """
    logger.error(f"Application error: {exc.message}")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": "Application Error",
            "message": exc.message
        }
    ) 