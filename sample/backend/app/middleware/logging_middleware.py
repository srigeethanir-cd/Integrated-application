"""Middleware for logging HTTP request timing and status metrics."""

import time
from app.core.logging import get_logger
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

logger = get_logger(__name__)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware measuring request execution time and logging HTTP access details."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        start_time = time.perf_counter()
        request_id = getattr(request.state, "request_id", "N/A")

        logger.info(
            "--> %s %s [ReqID: %s]",
            request.method,
            request.url.path,
            request_id,
        )

        try:
            response = await call_next(request)
            process_time_ms = (time.perf_counter() - start_time) * 1000
            logger.info(
                "<-- %s %s %d (%.2fms) [ReqID: %s]",
                request.method,
                request.url.path,
                response.status_code,
                process_time_ms,
                request_id,
            )
            response.headers["X-Process-Time-MS"] = f"{process_time_ms:.2f}"
            return response
        except Exception as exc:
            process_time_ms = (time.perf_counter() - start_time) * 1000
            logger.error(
                "<!- %s %s ERROR: %s (%.2fms) [ReqID: %s]",
                request.method,
                request.url.path,
                str(exc),
                process_time_ms,
                request_id,
            )
            raise exc
