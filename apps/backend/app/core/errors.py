from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
import logging

logger = logging.getLogger("campusgpt.errors")

class APIException(Exception):
    """Base API Exception for structured error outputs."""
    def __init__(self, status_code: int, code: str, message: str, details: dict | None = None):
        super().__init__(message)
        self.status_code = status_code
        self.code = code
        self.message = message
        self.details = details or {}

class ResourceNotFoundException(APIException):
    def __init__(self, message: str = "Resource not found", details: dict | None = None):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            code="RESOURCE_NOT_FOUND",
            message=message,
            details=details
        )

class ValidationException(APIException):
    def __init__(self, message: str = "Validation failed", details: dict | None = None):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            code="VALIDATION_FAILED",
            message=message,
            details=details
        )

def register_error_handlers(app: FastAPI) -> None:
    """Configures global exception handlers for the FastAPI application."""
    
    @app.exception_handler(APIException)
    async def api_exception_handler(request: Request, exc: APIException):
        logger.error(f"APIException ({exc.code}): {exc.message} - Details: {exc.details}")
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "success": False,
                "message": exc.message,
                "data": None,
                "errors": {
                    "code": exc.code,
                    "details": exc.details
                },
                "error": {
                    "code": exc.code,
                    "message": exc.message,
                    "details": exc.details
                }
            }
        )

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):
        logger.error(f"HTTPException ({exc.status_code}): {exc.detail}")
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "success": False,
                "message": exc.detail,
                "data": None,
                "errors": {
                    "code": f"HTTP_{exc.status_code}",
                    "details": {}
                },
                "error": {
                    "code": f"HTTP_{exc.status_code}",
                    "message": exc.detail,
                    "details": {}
                }
            }
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        # Format errors slightly nicer
        formatted_errors = []
        for error in exc.errors():
            loc = " -> ".join(str(x) for x in error.get("loc", []))
            msg = error.get("msg", "Invalid value")
            formatted_errors.append({"field": loc, "issue": msg})
            
        logger.warning(f"RequestValidationError: {formatted_errors}")
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "success": False,
                "message": "Invalid request payload schema",
                "data": None,
                "errors": {
                    "code": "REQUEST_VALIDATION_FAILED",
                    "details": {"errors": formatted_errors}
                },
                "error": {
                    "code": "REQUEST_VALIDATION_FAILED",
                    "message": "Invalid request payload schema",
                    "details": {"errors": formatted_errors}
                }
            }
        )

    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        logger.exception("Unhandled Internal Server Error occurred")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "success": False,
                "message": "An unexpected system error occurred.",
                "data": None,
                "errors": {
                    "code": "INTERNAL_SERVER_ERROR",
                    "details": {}
                },
                "error": {
                    "code": "INTERNAL_SERVER_ERROR",
                    "message": "An unexpected system error occurred.",
                    "details": {}
                }
            }
        )
