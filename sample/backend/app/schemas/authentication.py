"""Schemas for the migrated Authentication API contract."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class AuthenticationCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    data: dict[str, Any] = Field(default_factory=dict)


class AuthenticationUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    data: dict[str, Any] | None = None


class AuthenticationResponse(BaseModel):
    id: str
    name: str
    data: dict[str, Any]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AuthenticationPage(BaseModel):
    items: list[AuthenticationResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
