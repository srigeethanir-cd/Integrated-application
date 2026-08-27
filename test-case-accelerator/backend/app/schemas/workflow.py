"""Schemas for pipeline orchestration and explicit approval gates."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.code_understanding import CodeUnderstandingResponse
from app.schemas.dependency import DependencyRunDetail
from app.schemas.project import ProjectResponse
from app.schemas.security_scan import SecurityScanResponse
from app.schemas.code_understanding import TestGenerationResponse

WorkflowStage = Literal["stage_1", "stage_2", "stage_3", "stage_4"]
WorkflowStatus = Literal[
    "running", "completed", "waiting_for_approval", "failed"
]


class WorkflowResponse(BaseModel):
    """Persisted artifacts and approval state through Stage 3."""

    model_config = ConfigDict(extra="forbid")

    project: ProjectResponse
    current_stage: WorkflowStage
    status: WorkflowStatus
    completed_stage: WorkflowStage | None = None
    next_stage: WorkflowStage | None = None
    security_scan: SecurityScanResponse | None = None
    dependency: DependencyRunDetail | None = None
    pipeline: CodeUnderstandingResponse | None = None
    generation: TestGenerationResponse | None = None
    error: str | None = None
    logs: list[str] = Field(default_factory=list)


class WorkflowContinueRequest(BaseModel):
    """Approve execution of exactly one stage after ``from_stage``."""

    model_config = ConfigDict(extra="forbid")
    from_stage: WorkflowStage


class WorkflowResumeRequest(BaseModel):
    """Optional controls for the existing downstream resume API."""

    model_config = ConfigDict(extra="forbid")
    start_stage: Literal["test_generation"] | None = None
    force: bool = False
