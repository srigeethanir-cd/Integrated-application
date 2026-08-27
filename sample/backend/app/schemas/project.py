"""Project Pydantic v2 schemas."""

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field


class ProjectCreate(BaseModel):
    name: str = Field(description="Project name")
    description: Optional[str] = Field(default=None, description="Project description")
    tech_stack: str = Field(default="Python FastAPI / React TypeScript", description="Tech stack")


class ProjectUpdate(BaseModel):
    name: Optional[str] = Field(default=None)
    description: Optional[str] = Field(default=None)
    tech_stack: Optional[str] = Field(default=None)
    status: Optional[str] = Field(default=None)
    approval_mode: Optional[str] = Field(default=None)


class ProjectOut(BaseModel):
    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    name: str
    description: Optional[str] = None
    tech_stack: str = "Python FastAPI / React TypeScript"
    status: str = "ACTIVE"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
