"""Pydantic v2 schemas for Context Builder and Generation Context.

Defines the strongly typed contract returned by ``build_generation_context``.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.semantic import RecommendedAction, SemanticAnalysisResult

# Import only for type checking to avoid circular imports
if TYPE_CHECKING:
    from app.schemas.ba_accelerator import (
        BlueprintOut,
        ComponentOut,
        FileOut,
        StoryOut,
    )


# ────────────────────────────────────────────────────────────────────────
# Context Sub-Models
# ────────────────────────────────────────────────────────────────────────

class DependencyOut(BaseModel):
    """Schema for a component dependency relationship."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    component_id: uuid.UUID
    depends_on_component_id: uuid.UUID
    dependency_type: str


class GenerationHistoryOut(BaseModel):
    """Schema for agent audit history record."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    story_id: uuid.UUID
    agent: str
    action: str
    status: str
    execution_time: float | None = None
    timestamp: datetime


class StoryComponentMapOut(BaseModel):
    """Schema for story to component action mapping."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    story_id: uuid.UUID
    component_id: uuid.UUID
    action: str
    timestamp: datetime


class ValidationResultOut(BaseModel):
    """Schema for story validation outcome."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    story_id: uuid.UUID
    validation_type: str
    result: str
    report: dict[str, Any] | None = None
    validated_at: datetime


class TraceabilitySummary(BaseModel):
    """Aggregated traceability information for a story."""

    model_config = ConfigDict(from_attributes=True)

    story_id: uuid.UUID
    mapped_components: list[StoryComponentMapOut] = Field(default_factory=list)
    validations: list[ValidationResultOut] = Field(default_factory=list)
    file_changes: list[FileOut] = Field(default_factory=list)


# ────────────────────────────────────────────────────────────────────────
# Generation Context Root Schema
# ────────────────────────────────────────────────────────────────────────

class GenerationContext(BaseModel):
    """Strongly typed Pydantic container holding all context for code generation."""

    model_config = ConfigDict(from_attributes=True)

    story: StoryOut
    blueprint: BlueprintOut | None = None
    existing_components: list[ComponentOut] = Field(default_factory=list)
    shared_components: dict[str, Any] | list[dict[str, Any]] | None = Field(default_factory=dict)
    traceability: TraceabilitySummary
    dependencies: list[DependencyOut] = Field(default_factory=list)
    generation_history: list[GenerationHistoryOut] = Field(default_factory=list)
    files_to_modify: list[FileOut] = Field(default_factory=list)
    related_stories: list[StoryOut] = Field(default_factory=list)
    semantic_analysis: SemanticAnalysisResult | None = None
    recommended_action: RecommendedAction | str | None = None


# Resolve forward references for Pydantic v2 runtime validation
try:
    from .ba_accelerator import (
        BlueprintOut,
        ComponentOut,
        FileOut,
        StoryOut,
    )
    GenerationContext.model_rebuild(
        _types_namespace={
            "BlueprintOut": BlueprintOut,
            "ComponentOut": ComponentOut,
            "FileOut": FileOut,
            "StoryOut": StoryOut,
        }
    )
except Exception:
    pass


