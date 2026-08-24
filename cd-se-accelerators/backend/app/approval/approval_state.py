"""Approval state enums and impact analysis result models."""

from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ApprovalStatus(str, Enum):
    """Possible approval states for human-in-the-loop review."""

    PENDING = "PENDING"
    APPROVED = "APPROVED"
    CHANGES_REQUESTED = "CHANGES_REQUESTED"
    REJECTED = "REJECTED"


class ImpactAnalysisResult(BaseModel):
    """Represents impacted blueprint sections for targeted regeneration."""

    impacted_sections: List[str] = Field(
        default_factory=list,
        description="Impacted sections (e.g. api_contracts, database_schemas, frontend_mapping, epics, stories)",
    )
    unaffected_sections: List[str] = Field(
        default_factory=list,
        description="Unaffected sections that must NOT be regenerated",
    )
    impact_summary: str = Field(
        default="No impact detected", description="Summary explanation of change impact"
    )
