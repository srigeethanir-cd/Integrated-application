"""Structured Stage 6 quality evaluation schemas."""

import uuid
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.schemas.enums import Category
from app.schemas.test_case import TestCase, TestGenerationResult
from app.schemas.test_verification import TestVerificationResult


class RegenerationActionType(StrEnum):
    ADD = "ADD"
    UPDATE = "UPDATE"
    REMOVE = "REMOVE"


class RegenerationAction(BaseModel):
    model_config = ConfigDict(extra="forbid")

    action: RegenerationActionType
    test_case_id: str | None = None
    category: str | None = None
    target_symbol: str | None = None
    coverage_requirement: str | None = None

    @field_validator("category", mode="before")
    @classmethod
    def valid_category(cls, value):
        if value is None:
            return value
        mapping = {
            "functional": "positive", "regression": "positive",
            "edge_case": "boundary", "validation": "negative",
            "integration": "exception/integration", "exception": "exception/integration",
        }
        normalized = mapping.get(str(value).casefold(), str(value).casefold())
        return Category(normalized).value


class RegenerationPlan(BaseModel):
    model_config = ConfigDict(extra="forbid")

    current_score: float = Field(ge=0, le=100)
    threshold: float = Field(ge=0, le=100)
    missing_categories: list[str] = Field(default_factory=list)
    weak_test_cases: list[str] = Field(default_factory=list)
    failed_test_cases: list[str] = Field(default_factory=list)
    actions: list[RegenerationAction] = Field(default_factory=list)
    rationale: list[str] = Field(default_factory=list)

    @field_validator("missing_categories", mode="before")
    @classmethod
    def valid_missing_categories(cls, values):
        return [RegenerationAction.valid_category(value) for value in (values or [])]


class QualityDimensionScores(BaseModel):
    model_config = ConfigDict(extra="forbid")

    coverage: float = Field(ge=0, le=100)
    correctness: float = Field(ge=0, le=100)
    traceability: float = Field(ge=0, le=100)
    completeness: float = Field(ge=0, le=100)
    duplicates: float = Field(ge=0, le=100)
    maintainability: float = Field(ge=0, le=100)
    category_coverage: float = Field(ge=0, le=100)
    boundary_coverage: float = Field(default=0, ge=0, le=100)
    negative_testing: float = Field(default=0, ge=0, le=100)
    security: float = Field(default=0, ge=0, le=100)
    performance: float = Field(default=0, ge=0, le=100)
    duplicate_quality: float = Field(default=0, ge=0, le=100)


class QualityFeedback(BaseModel):
    model_config = ConfigDict(extra="forbid")

    weak_dimensions: list[str] = Field(default_factory=list)
    improve_test_case_ids: list[str] = Field(default_factory=list)
    replace_test_case_ids: list[str] = Field(default_factory=list)
    missing_categories: list[str] = Field(default_factory=list)
    instructions: list[str] = Field(default_factory=list)

    @field_validator("missing_categories", mode="before")
    @classmethod
    def valid_missing_categories(cls, values):
        return [RegenerationAction.valid_category(value) for value in (values or [])]


class QualityEvaluation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    overall_score: float = Field(ge=0, le=100)
    dimension_scores: QualityDimensionScores
    recommendations: list[str] = Field(default_factory=list)
    feedback: QualityFeedback
    threshold_met: bool
    iteration: int = Field(ge=1)
    regeneration_plan: RegenerationPlan | None = None


class QualityEvaluationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    code_understanding_run_id: uuid.UUID
    test_cases: list[TestCase]
    verification: TestVerificationResult


class QualityOptimizationRequest(QualityEvaluationRequest):
    """Run the independent Stage 6 iterative optimization loop."""


class QualityIterationSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    iteration: int = Field(ge=1)
    overall_score: float = Field(ge=0, le=100)
    verified: int = Field(ge=0)
    partial: int = Field(ge=0)
    failed: int = Field(ge=0)
    preserved: int = Field(ge=0)
    regenerated: int = Field(ge=0)
    threshold_met: bool


class QualityImprovementMetrics(BaseModel):
    model_config = ConfigDict(extra="forbid")

    initial_score: float = Field(ge=0, le=100)
    final_score: float = Field(ge=0, le=100)
    score_delta: float
    initial_verified: int = Field(ge=0)
    final_verified: int = Field(ge=0)
    verified_delta: int


class QualityLoopResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    test_generation: TestGenerationResult
    test_verification: TestVerificationResult
    quality_evaluation: QualityEvaluation
    iterations: int = Field(ge=1)
    optimized_test_cases: list[TestCase]
    evaluation_history: list[QualityEvaluation]
    iteration_summaries: list[QualityIterationSummary]
    improvement_metrics: QualityImprovementMetrics
    stopping_reason: str
    initial_score: float = Field(ge=0, le=100)
    final_score: float = Field(ge=0, le=100)
    regeneration_plans: list[RegenerationPlan]
    optimized_test_suite: list[TestCase]
    processing_status: str = "completed"
    resume_point: str | None = Field(
        default=None, exclude_if=lambda value: value is None
    )
    final_exit_reason: str | None = Field(
        default=None, exclude_if=lambda value: value is None
    )
    optimization_limit_reached: bool = False
    iterations_performed: int = Field(default=1, ge=1)
    configured_iteration_limit: int = Field(default=2, ge=1)
    executed_regeneration_batches: int = Field(default=0, ge=0)
    configured_regeneration_batch_limit: int = Field(default=2, ge=1)
    final_quality_score: float = Field(default=0, ge=0, le=100)
    stop_reason: str = ""
