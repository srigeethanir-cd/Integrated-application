from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ChangeImpactRequest(BaseModel):
    """Request payload to analyze change impact on test suites."""

    project_path: Optional[str] = Field(None, description="Absolute path to the project source directory.")
    changed_files: Optional[List[str]] = Field(None, description="List of relative or absolute paths of modified files.")
    pipeline_run_id: str = Field(..., description="Unique pipeline run identifier to retrieve context.")
    project_id: Optional[str] = Field(None, description="Unique project identifier.")


class TraceabilityStep(BaseModel):
    """A single step in the change impact traceability chain: Changed File -> Component -> IR -> Strategy -> Edge Case -> Test Case -> Test File."""

    changed_file: str = Field(..., description="The changed file path.")
    component: str = Field(..., description="Target component name.")
    ir_element: Optional[str] = Field(None, description="Affected IR element (event, state, route, etc.).")
    strategy: Optional[str] = Field(None, description="Test strategy applied.")
    edge_case: Optional[str] = Field(None, description="Edge case scenario name.")
    test_case_id: str = Field(..., description="Unique ID of the test case.")
    test_file: str = Field(..., description="Path of the test file where the test case is executed.")


class RecommendedTestCase(BaseModel):
    """Metadata for a recommended test case after impact analysis."""

    test_case_id: str = Field(..., description="Unique test case ID.")
    title: str = Field(..., description="Test case description.")
    component: str = Field(..., description="Name of the component under test.")
    category: str = Field(..., description="Test category (e.g. Forms, Accessibility).")
    priority: str = Field(..., description="Test priority level (High, Medium, Low).")
    impact_level: str = Field(..., description="Inferred impact level: HIGH, MEDIUM, LOW.")
    reason: str = Field(..., description="Rationale for selecting this test.")
    test_file: str = Field(..., description="Associated Jest test file name.")
    traceability: Optional[TraceabilityStep] = Field(None, description="Detailed traceability flow information.")


class ChangeImpactResponse(BaseModel):
    """Detailed change impact analysis outcome report."""

    total_tests: int = Field(..., description="Total tests in the suite.")
    impacted_tests: int = Field(..., description="Number of tests impacted by the changes.")
    unaffected_tests: int = Field(..., description="Number of tests not affected.")
    recommended_tests_count: int = Field(..., description="Number of recommended tests.")
    recommended_tests: List[RecommendedTestCase] = Field(default_factory=list, description="Detailed list of recommended test cases.")
    impact_score: float = Field(..., description="Calculated impact score from 0 to 100.")
    impact_level: str = Field(..., description="Inferred global impact level: HIGH, MEDIUM, LOW.")
    reasons: List[str] = Field(default_factory=list, description="Aggregated reasons for the impact rating.")
    estimated_reduction_percent: float = Field(..., description="Estimated test execution reduction percentage.")
    traceability: List[TraceabilityStep] = Field(default_factory=list, description="Traceability mappings.")
    
    # New Snapshot Automatic Diff fields
    project_id: Optional[str] = Field(None, description="Stable identifier of the project.")
    previous_snapshot_id: Optional[str] = Field(None, description="ID of the previous project snapshot.")
    current_snapshot_id: Optional[str] = Field(None, description="ID of the current project snapshot.")
    change_summary: Optional[Dict[str, int]] = Field(None, description="Count summary of added, modified, deleted, unchanged files.")
    first_upload: bool = Field(False, description="Flag indicating this is the project's baseline version.")
    deleted_components_traceability: List[TraceabilityStep] = Field(default_factory=list, description="Traceability steps for tests mapped to deleted component files.")


class RunImpactTestsRequest(BaseModel):
    """Payload to trigger execution on selected test files only."""

    pipeline_run_id: str = Field(..., description="Unique pipeline run identifier.")
    changed_files: Optional[List[str]] = Field(None, description="Optional changed files list to analyze and run immediately.")

