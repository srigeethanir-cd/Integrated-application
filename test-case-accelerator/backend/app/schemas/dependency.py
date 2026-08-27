# backend/app/schemas/dependency.py
"""Pydantic schemas for the Dependency discovery stage.

Only request/response models are defined. Business‑logic fields will be added
later.
"""

from __future__ import annotations

from enum import Enum as PyEnum
from pydantic import BaseModel, Field
from uuid import UUID
from typing import Any

from app.schemas.file_metadata import FileMetadata

class AnalysisStatusEnum(str, PyEnum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class DependencyRequest(BaseModel):
    """Request model to trigger a dependency discovery run.

    ``project_id`` is supplied by Stage 1. ``project_path`` is relative to the
    configured storage root.
    """

    project_id: str = Field(..., description="Identifier of the project from Stage 1")
    project_path: str = Field(..., description="Storage-root-relative source path")


class DependencyResponse(BaseModel):
    """Response returned after initiating a discovery run.

    ``run_id`` can be used to poll the status/result of the analysis.
    """

    run_id: UUID = Field(..., description="Unique identifier of the discovery run")
    status: AnalysisStatusEnum = Field(..., description="Current status of the run (pending, running, completed, failed)")

    model_config = {"from_attributes": True}


class DependencyRunDetail(DependencyResponse):
    project_id: UUID
    project_path: str
    files: list[FileMetadata]
    analysis: dict[str, Any] = Field(default_factory=dict)
