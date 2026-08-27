"""Core FastAPI dependency injection providers."""

from typing import Generator
from fastapi import Query, Request
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.database.session import get_db
from app.schemas.base import PaginationParams
from app.utils.llm_client import LLMClient


def get_current_settings() -> Settings:
    """Dependency providing cached application settings."""
    return get_settings()


def get_request_id(request: Request) -> str:
    """Dependency retrieving current X-Request-ID correlation ID."""
    return getattr(request.state, "request_id", "N/A")


def get_pagination_params(
    page: int = Query(default=1, ge=1, description="Page number"),
    size: int = Query(default=20, ge=1, le=100, description="Items per page"),
) -> PaginationParams:
    """Dependency parsing pagination query parameters."""
    return PaginationParams(page=page, size=size)


def get_llm_client() -> LLMClient:
    """Dependency instantiating shared LLM client."""
    return LLMClient()


__all__ = [
    "get_current_settings",
    "get_request_id",
    "get_pagination_params",
    "get_llm_client",
    "get_db",
]
