"""Generic, reusable Pydantic v2 base schemas and API envelopes."""

from datetime import datetime, timezone
from typing import Any, Generic, List, Optional, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class ErrorDetails(BaseModel):
    """Standardized error details payload."""

    code: str = Field(..., description="Application-specific error code")
    message: str = Field(..., description="Human-readable error summary")
    details: Optional[Any] = Field(default=None, description="Optional extra error metadata")


class APIResponse(BaseModel, Generic[T]):
    """Standard API response envelope."""

    success: bool = Field(default=True, description="Success status flag")
    data: Optional[T] = Field(default=None, description="Response payload")
    error: Optional[ErrorDetails] = Field(default=None, description="Error details if success is false")
    timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="ISO 8601 UTC timestamp",
    )
    request_id: Optional[str] = Field(default=None, description="Request correlation ID")


class PaginationParams(BaseModel):
    """Query parameter model for list pagination."""

    page: int = Field(default=1, ge=1, description="Page number starting at 1")
    size: int = Field(default=20, ge=1, le=100, description="Items per page (max 100)")

    @property
    def skip(self) -> int:
        """Calculate offset skip index."""
        return (self.page - 1) * self.size


class PaginationMeta(BaseModel):
    """Pagination metadata model."""

    total: int = Field(..., description="Total matching items")
    page: int = Field(..., description="Current page number")
    size: int = Field(..., description="Page size limit")
    pages: int = Field(..., description="Total pages available")
    has_next: bool = Field(..., description="Whether a next page exists")
    has_prev: bool = Field(..., description="Whether a previous page exists")


class PaginatedData(BaseModel, Generic[T]):
    """Container for paginated items and metadata."""

    items: List[T] = Field(default_factory=list, description="List of page items")
    pagination: PaginationMeta = Field(..., description="Pagination metadata")


class PaginatedResponse(APIResponse[PaginatedData[T]], Generic[T]):
    """Standard response envelope for paginated list endpoints."""

    pass


class MessageResponse(BaseModel):
    """Simple message response model."""

    message: str = Field(..., description="Informational or success message")


class HealthCheckResponse(BaseModel):
    """System health check status payload."""

    status: str = Field(default="healthy", description="System operational status")
    version: str = Field(..., description="API version")
    timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="Current server UTC timestamp",
    )
