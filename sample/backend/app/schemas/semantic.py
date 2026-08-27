"""Pydantic v2 schemas for Semantic Analyzer inside Knowledge Service."""

from __future__ import annotations

import uuid
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class ChangeType(str, Enum):
    """Classification type for how a story relates to the existing project."""

    NEW_FEATURE = "NEW_FEATURE"
    MODIFICATION = "MODIFICATION"
    EXTENSION = "EXTENSION"
    DUPLICATE = "DUPLICATE"


class RecommendedAction(str, Enum):
    """Recommended action for downstream code generation agents."""

    CREATE = "CREATE"
    MODIFY = "MODIFY"
    REUSE = "REUSE"
    IGNORE = "IGNORE"


class SemanticAnalysisResult(BaseModel):
    """Strongly typed output model returned by SemanticAnalyzer.analyze_story."""

    model_config = ConfigDict(from_attributes=True)

    change_type: ChangeType = Field(
        ..., description="Classification of how the story relates to the existing project."
    )
    confidence_score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Confidence score of the semantic analysis (0.0 to 1.0).",
    )
    matched_story_ids: list[uuid.UUID | str] = Field(
        default_factory=list,
        description="IDs or keys of existing stories that match or relate to this story.",
    )
    impacted_components: list[str] = Field(
        default_factory=list,
        description="Names or IDs of existing components impacted by this story.",
    )
    impacted_files: list[str] = Field(
        default_factory=list,
        description="File paths impacted or marked for modification.",
    )
    reasoning: str = Field(
        ..., description="Detailed explanation supporting the classification."
    )
    recommended_action: RecommendedAction = Field(
        ..., description="Recommended action: CREATE | MODIFY | REUSE | IGNORE."
    )
