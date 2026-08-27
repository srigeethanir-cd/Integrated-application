"""Application exceptions and global FastAPI exception handlers."""

import logging
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)


class AppError(Exception):
    """Base application exception."""

    status_code: int = status.HTTP_400_BAD_REQUEST
    error_code: str = "BAD_REQUEST"

    def __init__(
        self,
        detail: str = "An application error occurred",
        error_code: Optional[str] = None,
        extra: Optional[Dict[str, Any]] = None,
    ) -> None:
        self.detail = detail
        self.error_code = error_code or self.error_code
        self.extra = extra or {}
        super().__init__(detail)


class NotFoundError(AppError):
    """Resource not found exception."""

    status_code: int = status.HTTP_404_NOT_FOUND
    error_code: str = "NOT_FOUND"

    def __init__(self, resource: str = "Resource", identifier: Optional[Any] = None) -> None:
        detail = f"{resource} not found" if not identifier else f"{resource} '{identifier}' not found"
        super().__init__(detail=detail)


class ValidationError(AppError):
    """Business validation error exception."""

    status_code: int = 422
    error_code: str = "VALIDATION_ERROR"


class UnauthorizedError(AppError):
    """Authentication required exception."""

    status_code: int = status.HTTP_401_UNAUTHORIZED
    error_code: str = "UNAUTHORIZED"

    def __init__(self, detail: str = "Authentication credentials required") -> None:
        super().__init__(detail=detail)


class ForbiddenError(AppError):
    """Access forbidden exception."""

    status_code: int = status.HTTP_403_FORBIDDEN
    error_code: str = "FORBIDDEN"

    def __init__(self, detail: str = "Operation forbidden") -> None:
        super().__init__(detail=detail)


class ConflictError(AppError):
    """Resource conflict exception."""

    status_code: int = status.HTTP_409_CONFLICT
    error_code: str = "CONFLICT"


class DatabaseError(AppError):
    """Database operation exception."""

    status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR
    error_code: str = "DATABASE_ERROR"


class LLMServiceError(AppError):
    """LLM provider service failure exception."""

    status_code: int = status.HTTP_502_BAD_GATEWAY
    error_code: str = "LLM_SERVICE_ERROR"


def create_error_payload(
    message: str,
    error_code: str,
    status_code: int,
    request_id: Optional[str] = None,
    details: Optional[Any] = None,
) -> Dict[str, Any]:
    """Format standardized error envelope."""
    return {
        "success": False,
        "data": None,
        "error": {
            "code": error_code,
            "message": message,
            "details": details,
        },
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "request_id": request_id,
    }


def register_exception_handlers(app: FastAPI) -> None:
    """Register custom exception handlers with FastAPI application instance."""

    @app.exception_handler(AppError)
    async def handle_app_error(request: Request, exc: AppError) -> JSONResponse:
        request_id = getattr(request.state, "request_id", None)
        logger.warning(
            "AppError [%s] HTTP %d: %s (Request ID: %s)",
            exc.error_code,
            exc.status_code,
            exc.detail,
            request_id,
        )
        payload = create_error_payload(
            message=exc.detail,
            error_code=exc.error_code,
            status_code=exc.status_code,
            request_id=request_id,
            details=exc.extra,
        )
        return JSONResponse(status_code=exc.status_code, content=payload)

    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(request: Request, exc: RequestValidationError) -> JSONResponse:
        request_id = getattr(request.state, "request_id", None)
        logger.warning("RequestValidationError on %s (Request ID: %s)", request.url.path, request_id)
        payload = create_error_payload(
            message="Request body or query validation failed",
            error_code="VALIDATION_ERROR",
            status_code=422,
            request_id=request_id,
            details=exc.errors(),
        )
        return JSONResponse(status_code=422, content=payload)

    @app.exception_handler(Exception)
    async def handle_unhandled_error(request: Request, exc: Exception) -> JSONResponse:
        request_id = getattr(request.state, "request_id", None)
        logger.exception("Unhandled Exception on %s (Request ID: %s): %s", request.url.path, request_id, str(exc))
        payload = create_error_payload(
            message="An unexpected internal server error occurred",
            error_code="INTERNAL_SERVER_ERROR",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            request_id=request_id,
        )
        return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content=payload)
