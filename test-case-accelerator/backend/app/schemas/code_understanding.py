"""Transport schemas for Stage 3 code understanding."""

import uuid

from pydantic import BaseModel, ConfigDict

from app.agents.code_understanding.agent import (
    CodeUnderstandingResult,
    CodeUnderstandingWithRuntimePreparationResult,
    CodeUnderstandingWithOptimizationResult,
    CodeUnderstandingWithTestsResult,
    CodeUnderstandingWithVerificationResult,
    CodeUnderstandingWithQualityResult,
)
from app.database.models.code_understanding import CodeUnderstandingStatus
from app.schemas.test_case import TestCase, TestGenerationResult
from app.schemas.test_verification import TestVerificationResult
from app.schemas.dependency import DependencyRunDetail
from app.schemas.test_quality import QualityLoopResult
from app.schemas.runtime_preparation import RuntimeExecutionPlan
from app.schemas.security_scan import SecurityScanResponse


class CodeUnderstandingRequest(BaseModel):
    dependency_run_id: uuid.UUID


class CodeUnderstandingResponse(BaseModel):
    run_id: uuid.UUID
    status: CodeUnderstandingStatus
    result: (
        CodeUnderstandingWithRuntimePreparationResult
        | CodeUnderstandingWithOptimizationResult
        | CodeUnderstandingWithQualityResult
        | CodeUnderstandingWithVerificationResult
        | CodeUnderstandingWithTestsResult
        | CodeUnderstandingResult
        | None
    ) = None
    failed_stage: str | None = None
    failure_reason: str | None = None
    retry_count: int = 0
    last_successful_stage: str | None = None

    model_config = {"from_attributes": True}


class TestGenerationRequest(BaseModel):
    """Run Stage 4 from a completed Stage 3 artifact."""

    model_config = ConfigDict(extra="forbid")
    code_understanding_run_id: uuid.UUID


class TestGenerationResponse(TestGenerationResult):
    """Standalone Stage 4 output."""


class TestVerificationRequest(BaseModel):
    """Run Stage 5 for Stage 4-compatible test cases."""

    model_config = ConfigDict(extra="forbid")
    code_understanding_run_id: uuid.UUID
    test_cases: list[TestCase]


class TestVerificationResponse(TestVerificationResult):
    """Standalone Stage 5 output."""


class PipelineStateResponse(BaseModel):
    """Latest persisted Stage 2-6 artifacts for a project."""

    project_id: uuid.UUID
    security_scan: SecurityScanResponse | None = None
    dependency: DependencyRunDetail | None = None
    understanding: CodeUnderstandingResponse | None = None
    generation: TestGenerationResponse | None = None
    verification: TestVerificationResponse | None = None
    quality: QualityLoopResult | None = None
    runtime_preparation: RuntimeExecutionPlan | None = None
    failed_stage: str | None = None
    failure_reason: str | None = None
    retry_count: int = 0
    last_successful_stage: str | None = None
    resumed_stage: str | None = None
