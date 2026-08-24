"""Pydantic v2 schemas for API request / response serialization.

These schemas are the public contract — they decouple the API surface
from the internal SQLAlchemy ORM models.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


# ────────────────────────────────────────────────────────────────────────
# Project
# ────────────────────────────────────────────────────────────────────────

class ProjectCreate(BaseModel):
    name: str = Field(..., max_length=255, examples=["E-Commerce Platform"])
    description: str | None = Field(None, examples=["Online retail platform with microservices"])
    status: str = Field("draft", max_length=50, examples=["draft"])


class ProjectUpdate(BaseModel):
    name: str | None = Field(None, max_length=255)
    description: str | None = None
    status: str | None = Field(None, max_length=50)
    approval_mode: str | None = Field(None, max_length=50)
    tech_stack: Any | None = None


class ProjectOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    description: str | None
    status: str
    created_at: datetime
    updated_at: datetime


# ────────────────────────────────────────────────────────────────────────
# Blueprint
# ────────────────────────────────────────────────────────────────────────

class BlueprintCreate(BaseModel):
    project_id: uuid.UUID
    version: int = Field(1, ge=1)
    architecture: str | None = None
    folder_structure: dict[str, Any] | None = None
    api_blueprint: dict[str, Any] | None = None
    workflow_blueprint: dict[str, Any] | None = None
    shared_components: dict[str, Any] | None = None


class BlueprintUpdate(BaseModel):
    version: int | None = Field(None, ge=1)
    architecture: str | None = None
    folder_structure: dict[str, Any] | None = None
    api_blueprint: dict[str, Any] | None = None
    workflow_blueprint: dict[str, Any] | None = None
    shared_components: dict[str, Any] | None = None


class BlueprintOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    project_id: uuid.UUID
    version: int
    architecture: str | None
    folder_structure: dict[str, Any] | None
    api_blueprint: dict[str, Any] | None
    workflow_blueprint: dict[str, Any] | None
    shared_components: dict[str, Any] | None
    created_at: datetime


# ────────────────────────────────────────────────────────────────────────
# Epic
# ────────────────────────────────────────────────────────────────────────

class EpicCreate(BaseModel):
    project_id: uuid.UUID
    blueprint_id: uuid.UUID
    epic_key: str = Field(..., max_length=50, examples=["EPIC-001"])
    title: str = Field(..., max_length=500, examples=["User Authentication"])
    description: str | None = None
    priority: str | None = Field(None, max_length=20, examples=["high"])


class EpicUpdate(BaseModel):
    title: str | None = Field(None, max_length=500)
    description: str | None = None
    priority: str | None = Field(None, max_length=20)


class EpicOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    project_id: uuid.UUID
    blueprint_id: uuid.UUID
    epic_key: str
    title: str
    description: str | None
    priority: str | None
    created_at: datetime


# ────────────────────────────────────────────────────────────────────────
# Story
# ────────────────────────────────────────────────────────────────────────

class StoryCreate(BaseModel):
    epic_id: uuid.UUID | str | None = None
    story_key: str = Field(..., max_length=50, examples=["US-001"])
    title: str = Field(..., max_length=500, examples=["User can sign up"])
    description: str | None = None
    acceptance_criteria: dict[str, Any] | None = Field(
        None, examples=[{"criteria": ["User can create account", "Email sent"]}],
    )
    status: str = Field("pending", max_length=50)
    approved: bool = False


class StoryUpdate(BaseModel):
    title: str | None = Field(None, max_length=500)
    description: str | None = None
    acceptance_criteria: dict[str, Any] | None = None
    status: str | None = Field(None, max_length=50)
    approved: bool | None = None


class StoryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID | str
    epic_id: uuid.UUID | str | None = None
    story_key: str | None = None
    title: str
    description: str | None = None
    acceptance_criteria: dict[str, Any] | None = None
    status: str = "pending"
    approved: bool = False
    created_at: datetime | str | None = None


# ────────────────────────────────────────────────────────────────────────
# Component
# ────────────────────────────────────────────────────────────────────────

class ComponentCreate(BaseModel):
    project_id: uuid.UUID
    name: str = Field(..., max_length=255, examples=["AuthService"])
    type: str = Field(..., max_length=100, examples=["service"])
    path: str | None = Field(None, max_length=1000, examples=["src/services/auth"])
    description: str | None = None
    created_by_agent: str | None = Field(None, max_length=50, examples=["agent1"])


class ComponentUpdate(BaseModel):
    name: str | None = Field(None, max_length=255)
    type: str | None = Field(None, max_length=100)
    path: str | None = Field(None, max_length=1000)
    description: str | None = None
    created_by_agent: str | None = Field(None, max_length=50)


class ComponentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    project_id: uuid.UUID
    name: str
    type: str
    path: str | None
    description: str | None
    created_by_agent: str | None
    created_at: datetime


# ────────────────────────────────────────────────────────────────────────
# File
# ────────────────────────────────────────────────────────────────────────

class FileCreate(BaseModel):
    component_id: uuid.UUID
    story_id: uuid.UUID
    path: str = Field(..., max_length=1000, examples=["src/services/auth/handler.py"])
    hash: str | None = Field(None, max_length=128)
    version: int = Field(1, ge=1)


class FileUpdate(BaseModel):
    path: str | None = Field(None, max_length=1000)
    hash: str | None = Field(None, max_length=128)
    version: int | None = Field(None, ge=1)


class FileOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    component_id: uuid.UUID | None = None
    story_id: uuid.UUID | None = None
    path: str
    hash: str | None = None
    version: int
    created_at: datetime


# Re-export context & semantic schemas
from app.schemas.context import (  # noqa: E402
    DependencyOut,
    GenerationContext,
    GenerationHistoryOut,
    StoryComponentMapOut,
    TraceabilitySummary,
    ValidationResultOut,
)
from app.schemas.semantic import (  # noqa: E402
    ChangeType,
    RecommendedAction,
    SemanticAnalysisResult,
)


class RequestChangeCreate(BaseModel):
    project_id: uuid.UUID | str
    blueprint_id: uuid.UUID | str | None = None
    blueprint_version: int | None = None
    location_type: str
    target_id: str | None = None
    target_path: str | None = None
    field_name: str | None = None
    original_value: str | None = None
    requested_change: str
    modified_prompt: str | None = None
    modified_value: str | None = None
    status: str = "PENDING"
    created_by: str | None = "Business Analyst"


class RequestChangeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    request_change_id: uuid.UUID
    project_id: uuid.UUID
    blueprint_id: uuid.UUID | None = None
    blueprint_version: int | None = None
    location_type: str
    target_id: str | None = None
    target_path: str | None = None
    field_name: str | None = None
    original_value: str | None = None
    requested_change: str
    modified_prompt: str | None = None
    modified_value: str | None = None
    status: str
    created_by: str | None = None
    created_at: datetime
    updated_at: datetime

