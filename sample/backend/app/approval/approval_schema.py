"""Approval request, report, history, and artifacts review schemas."""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from app.approval.approval_state import ApprovalStatus, ImpactAnalysisResult


class ApprovalReviewRequest(BaseModel):
    """Payload submitted by the Business Analyst during human review."""

    status: ApprovalStatus = Field(description="Selected approval status: APPROVED | CHANGES_REQUESTED | REJECTED")
    reviewer: str = Field(default="Business Analyst", description="Name/ID of the human reviewer")
    comments: str = Field(default="", description="Reviewer feedback or change instructions")
    impacted_sections: Optional[List[str]] = Field(
        default=None,
        description="Explicit list of impacted blueprint sections if CHANGES_REQUESTED",
    )


class ValidationResultItem(BaseModel):
    """Validation status item for each of the 10 architecture criteria."""

    criterion: str = Field(description="Architectural aspect name")
    passed: bool = Field(description="Validation status")
    details: str = Field(description="Validation check explanation")


class ApprovalReportResponse(BaseModel):
    """Detailed approval report payload."""

    project_name: str = Field(description="Target project name")
    blueprint_version: str = Field(description="Blueprint version string")
    readiness_score: float = Field(description="Architecture readiness score (0-100%)")
    validation_checks: List[ValidationResultItem] = Field(default_factory=list)
    overall_passed: bool = Field(description="Whether all 10 architectural criteria passed")
    summary: Dict[str, Any] = Field(default_factory=dict, description="Artifact summaries")


class ApprovalHistoryRecord(BaseModel):
    """Historical audit record for an approval cycle."""

    cycle_id: str = Field(description="Unique cycle ID")
    blueprint_version: str = Field(description="Blueprint version")
    reviewer: str = Field(description="Reviewer name/role")
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    comments: str = Field(description="Reviewer comments")
    status: ApprovalStatus = Field(description="Resulting approval status")
    change_summary: str = Field(description="Summary of requested changes")
    impact_analysis: ImpactAnalysisResult = Field(description="Impact analysis metadata")


class ArtifactsReviewBundle(BaseModel):
    """Bundle containing all 10 architecture artifacts for BA review."""

    project_name: str
    blueprint_version: str
    requirement_json: Dict[str, Any]
    configuration_json: Dict[str, Any]
    generated_frontend: Dict[str, Any]
    master_blueprint: Dict[str, Any]
    folder_structure: List[str]
    workspace_manifest: Dict[str, Any]
    dependency_graph: Dict[str, Any]
    api_blueprint: List[Dict[str, Any]]
    database_blueprint: List[Dict[str, Any]]
    traceability_map: Dict[str, Any]
