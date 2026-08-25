"""
Validation Models – Module 9.

Defines Pydantic models for testing validation, static code quality scoring,
code coverage auditing, and E2E system health summaries.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from app.models.test_writer_models import TestWriterResponse


class ValidationRequest(BaseModel):
    """Payload to trigger E2E validation and quality auditing on generated files."""

    project_path: Optional[str] = Field(None, description="Absolute path to target workspace directory containing tests and manifest.")
    framework: Optional[str] = Field("React", description="Framework under validation: React, Angular.")
    generated_test_files: Optional[TestWriterResponse] = Field(None, description="Optional TestWriterResponse artifact from Module 8.")


class CoverageStats(BaseModel):
    """Normalized code coverage metrics."""

    statements: float = Field(..., ge=0, le=100, description="Percentage of statement coverage.")
    branches: float = Field(..., ge=0, le=100, description="Percentage of branch coverage.")
    functions: float = Field(..., ge=0, le=100, description="Percentage of function coverage.")
    lines: float = Field(..., ge=0, le=100, description="Percentage of line coverage.")


class BehaviorCoverageBreakdown(BaseModel):
    """Behavioral coverage metrics breakdown derived from semantic IR auditing."""

    behavior_coverage: float = Field(..., ge=0, le=100, description="Overall component behavior coverage percentage.")
    interaction_coverage: float = Field(..., ge=0, le=100, description="Interaction graph node coverage percentage.")
    state_transition_coverage: float = Field(..., ge=0, le=100, description="State transition path coverage percentage.")
    conditional_rendering_coverage: float = Field(..., ge=0, le=100, description="Conditional rendering visibility rule coverage percentage.")
    accessibility_coverage: float = Field(..., ge=0, le=100, description="WCAG accessibility checklist coverage percentage.")
    hook_coverage: float = Field(..., ge=0, le=100, description="React hook dependency/lifecycle coverage percentage.")
    event_coverage: float = Field(..., ge=0, le=100, description="Event handler binding coverage percentage.")
    risk_coverage: float = Field(..., ge=0, le=100, description="High and medium risk feature coverage percentage.")


class QualityGapsAudit(BaseModel):
    """Quality gap defect metrics audit."""

    duplicate_scenarios: int = Field(0, ge=0, description="Count of duplicate test scenario titles/keys.")
    redundant_assertions: int = Field(0, ge=0, description="Count of duplicate or redundant assert statements.")
    missing_negative_tests: int = Field(0, ge=0, description="Count of untested failure/error boundary paths.")
    missing_boundary_tests: int = Field(0, ge=0, description="Count of missing boundary conditions.")
    missing_accessibility_tests: int = Field(0, ge=0, description="Count of missing accessibility audits for interactive components.")
    missing_async_tests: int = Field(0, ge=0, description="Count of unhandled async/promise resolution edge cases.")
    missing_cleanup: int = Field(0, ge=0, description="Count of test files missing afterEach/cleanup teardown hooks.")
    missing_mocks: int = Field(0, ge=0, description="Count of unmocked external service/network dependencies.")


class ValidationReport(BaseModel):
    """Detailed summary of compilation, execution, quality audits, behavior metrics, and coverage runs."""

    framework: str = Field(..., description="Underlying framework: React, Angular.")
    total_files: int = Field(..., ge=0, description="Total number of checked files.")
    compiled: bool = Field(..., description="True if compile checks passed on all test files.")
    tests_passed: int = Field(..., ge=0, description="Total number of successfully executed unit tests.")
    tests_failed: int = Field(..., ge=0, description="Total number of failed unit tests.")
    tests_skipped: int = Field(..., ge=0, description="Total number of skipped unit tests.")
    coverage: CoverageStats = Field(..., description="Statement, branch, function, and line coverage metrics.")
    quality_score: float = Field(..., ge=0, le=100, description="Static code quality audit score.")
    coverage_percentage: float = Field(85.0, ge=0, le=100, description="Real behavior coverage percentage.")
    duplicate_score: float = Field(100.0, ge=0, le=100, description="Deduplication efficiency score.")
    maintainability_score: float = Field(90.0, ge=0, le=100, description="Code maintainability index score.")
    confidence_score: float = Field(85.0, ge=0, le=100, description="Overall test suite confidence rating.")
    validation_passed: bool = Field(..., description="True if compiler and coverage goals were successfully met.")
    behavior_breakdown: Optional[BehaviorCoverageBreakdown] = Field(None, description="Detailed behavioral coverage breakdown.")
    quality_gaps: Optional[QualityGapsAudit] = Field(None, description="Quality gaps audit details.")
    recommendations: List[str] = Field(default_factory=list, description="Actionable test quality recommendations.")
    errors: List[str] = Field(default_factory=list, description="Detail list of errors.")
    warnings: List[str] = Field(default_factory=list, description="Detail list of warnings.")
