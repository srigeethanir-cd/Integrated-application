"""Middleware package and registration helper."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.middleware.logging_middleware import RequestLoggingMiddleware
from app.middleware.request_id import RequestIDMiddleware


def register_middlewares(app: FastAPI) -> None:
    """Register all application middlewares on a FastAPI application instance."""
    settings = get_settings()

    # Request ID Middleware (Outer)
    app.add_middleware(RequestIDMiddleware)

    # Logging Middleware
    app.add_middleware(RequestLoggingMiddleware)

    # CORS Middleware
    origins = settings.cors_origins
    if isinstance(origins, str):
        origins = [origins]

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins or ["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


__all__ = ["RequestIDMiddleware", "RequestLoggingMiddleware", "register_middlewares"]
