"""Standard HTTP response helper utilities."""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi.responses import JSONResponse


def success_response(
    data: Any = None,
    status_code: int = 200,
    message: Optional[str] = None,
    request_id: Optional[str] = None,
) -> JSONResponse:
    """Construct a standard JSON success response envelope."""
    payload: Dict[str, Any] = {
        "success": True,
        "data": data,
        "error": None,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "request_id": request_id,
    }
    if message:
        payload["message"] = message
    return JSONResponse(status_code=status_code, content=payload)


def error_response(
    message: str,
    error_code: str = "BAD_REQUEST",
    status_code: int = 400,
    details: Optional[Any] = None,
    request_id: Optional[str] = None,
) -> JSONResponse:
    """Construct a standard JSON error response envelope."""
    payload: Dict[str, Any] = {
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
    return JSONResponse(status_code=status_code, content=payload)


def paginated_response(
    items: List[Any],
    total: int,
    page: int,
    size: int,
    status_code: int = 200,
    request_id: Optional[str] = None,
) -> JSONResponse:
    """Construct a standard paginated JSON success response envelope."""
    pages = (total + size - 1) // size if size > 0 else 0
    payload: Dict[str, Any] = {
        "success": True,
        "data": {
            "items": items,
            "pagination": {
                "total": total,
                "page": page,
                "size": size,
                "pages": pages,
                "has_next": page < pages,
                "has_prev": page > 1,
            },
        },
        "error": None,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "request_id": request_id,
    }
    return JSONResponse(status_code=status_code, content=payload)
