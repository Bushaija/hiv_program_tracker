from typing import Any, Dict, Optional, Union
from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse
from fastapi.exception_handlers import http_exception_handler
import logging

logger = logging.getLogger(__name__)


# Custom Exception Classes
class BaseAPIException(Exception):
    """Base exception class for all API exceptions."""
    
    def __init__(
        self,
        message: str = "An error occurred",
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        details: Optional[Dict[str, Any]] = None,
        error_code: Optional[str] = None,
    ):
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        self.error_code = error_code
        super().__init__(self.message)


class ValidationError(BaseAPIException):
    """Raised when validation fails."""
    
    def __init__(self, message: str = "Validation failed", details: Optional[Dict] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            details=details,
            error_code="VALIDATION_ERROR"
        )


class NotFoundError(BaseAPIException):
    """Raised when a resource is not found."""
    
    def __init__(self, message: str = "Resource not found", resource: Optional[str] = None):
        details = {"resource": resource} if resource else {}
        super().__init__(
            message=message,
            status_code=status.HTTP_404_NOT_FOUND,
            details=details,
            error_code="NOT_FOUND"
        )


class AuthenticationError(BaseAPIException):
    """Raised when authentication fails."""
    
    def __init__(self, message: str = "Authentication failed"):
        super().__init__(
            message=message,
            status_code=status.HTTP_401_UNAUTHORIZED,
            error_code="AUTHENTICATION_ERROR"
        )


class AuthorizationError(BaseAPIException):
    """Raised when authorization fails."""
    
    def __init__(self, message: str = "Insufficient permissions"):
        super().__init__(
            message=message,
            status_code=status.HTTP_403_FORBIDDEN,
            error_code="AUTHORIZATION_ERROR"
        )


class ConflictError(BaseAPIException):
    """Raised when there's a conflict with existing data."""
    
    def __init__(self, message: str = "Resource conflict", resource: Optional[str] = None):
        details = {"resource": resource} if resource else {}
        super().__init__(
            message=message,
            status_code=status.HTTP_409_CONFLICT,
            details=details,
            error_code="CONFLICT_ERROR"
        )


class BusinessLogicError(BaseAPIException):
    """Raised when business logic validation fails."""
    
    def __init__(self, message: str = "Business logic validation failed", details: Optional[Dict] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_400_BAD_REQUEST,
            details=details,
            error_code="BUSINESS_LOGIC_ERROR"
        )


class DatabaseError(BaseAPIException):
    """Raised when database operations fail."""
    
    def __init__(self, message: str = "Database operation failed", operation: Optional[str] = None):
        details = {"operation": operation} if operation else {}
        super().__init__(
            message=message,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            details=details,
            error_code="DATABASE_ERROR"
        )


class ExternalServiceError(BaseAPIException):
    """Raised when external service calls fail."""
    
    def __init__(self, message: str = "External service error", service: Optional[str] = None):
        details = {"service": service} if service else {}
        super().__init__(
            message=message,
            status_code=status.HTTP_502_BAD_GATEWAY,
            details=details,
            error_code="EXTERNAL_SERVICE_ERROR"
        )


class RateLimitError(BaseAPIException):
    """Raised when rate limits are exceeded."""
    
    def __init__(self, message: str = "Rate limit exceeded"):
        super().__init__(
            message=message,
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            error_code="RATE_LIMIT_ERROR"
        )


# Exception Handlers
async def api_exception_handler(request: Request, exc: BaseAPIException) -> JSONResponse:
    """Handler for custom API exceptions."""
    
    logger.error(
        f"API Exception: {exc.error_code} - {exc.message}",
        extra={
            "error_code": exc.error_code,
            "status_code": exc.status_code,
            "details": exc.details,
            "path": request.url.path,
            "method": request.method,
        }
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "message": exc.message,
                "code": exc.error_code,
                "details": exc.details,
                "timestamp": str(exc.__class__.__name__),
            }
        },
    )


async def validation_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handler for Pydantic validation exceptions."""
    from pydantic import ValidationError as PydanticValidationError
    
    if isinstance(exc, PydanticValidationError):
        logger.warning(
            f"Validation error on {request.url.path}: {exc.errors()}",
            extra={"validation_errors": exc.errors()}
        )
        
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "error": {
                    "message": "Validation failed",
                    "code": "VALIDATION_ERROR",
                    "details": {"validation_errors": exc.errors()},
                }
            },
        )
    
    # Re-raise if it's not a Pydantic validation error
    raise exc


async def http_exception_override_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """Override default HTTP exception handler to maintain consistent error format."""
    
    logger.warning(
        f"HTTP Exception: {exc.status_code} - {exc.detail}",
        extra={
            "status_code": exc.status_code,
            "path": request.url.path,
            "method": request.method,
        }
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "message": exc.detail,
                "code": "HTTP_ERROR",
                "details": {},
            }
        },
    )


async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handler for unexpected exceptions."""
    
    logger.error(
        f"Unexpected error on {request.url.path}: {str(exc)}",
        exc_info=True,
        extra={
            "path": request.url.path,
            "method": request.method,
        }
    )
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": {
                "message": "Internal server error",
                "code": "INTERNAL_ERROR",
                "details": {},
            }
        },
    )


# Utility functions for raising common exceptions
def raise_not_found(resource: str, identifier: Union[str, int] = None) -> None:
    """Convenience function to raise NotFoundError."""
    message = f"{resource} not found"
    if identifier:
        message += f" with identifier: {identifier}"
    raise NotFoundError(message=message, resource=resource)


def raise_conflict(resource: str, field: str = None, value: str = None) -> None:
    """Convenience function to raise ConflictError."""
    message = f"{resource} already exists"
    if field and value:
        message += f" with {field}: {value}"
    raise ConflictError(message=message, resource=resource)


def raise_validation_error(field: str, message: str) -> None:
    """Convenience function to raise ValidationError."""
    raise ValidationError(
        message=f"Validation failed for field: {field}",
        details={"field": field, "error": message}
    )


def raise_business_logic_error(message: str, **details) -> None:
    """Convenience function to raise BusinessLogicError."""
    raise BusinessLogicError(message=message, details=details)


# Error response models for OpenAPI documentation
from pydantic import BaseModel
from typing import Any


class ErrorDetail(BaseModel):
    message: str
    code: str
    details: Dict[str, Any] = {}


class ErrorResponse(BaseModel):
    error: ErrorDetail
    
    class Config:
        schema_extra = {
            "example": {
                "error": {
                    "message": "Resource not found",
                    "code": "NOT_FOUND",
                    "details": {"resource": "User"}
                }
            }
        }


# Common error responses for OpenAPI
COMMON_RESPONSES = {
    400: {"model": ErrorResponse, "description": "Bad Request"},
    401: {"model": ErrorResponse, "description": "Unauthorized"},
    403: {"model": ErrorResponse, "description": "Forbidden"},
    404: {"model": ErrorResponse, "description": "Not Found"},
    409: {"model": ErrorResponse, "description": "Conflict"},
    422: {"model": ErrorResponse, "description": "Validation Error"},
    500: {"model": ErrorResponse, "description": "Internal Server Error"},
}