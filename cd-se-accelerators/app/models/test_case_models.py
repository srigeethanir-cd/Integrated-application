"""
Test Case Models – Module 7.

Defines Pydantic models for structured, framework-agnostic test cases
generated from Strategy and Edge Case plans.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field, field_validator

from app.models.ir_models import FrameworkAgnosticIR
from app.models.strategy_models import StrategyPlanResponse
from app.models.edge_case_models import EdgeCasePlanResponse


class TestCaseLocator(BaseModel):
    """Locator for finding a target element in the view."""

    strategy: str = Field(..., description="Locator strategy: role, label, css, id, tag, state_variable, dependency_injection, url_path, accessibility_role, etc.")
    value: str = Field(..., description="Target query identifier value.")


class TestCaseMetadata(BaseModel):
    """Enriched framework-agnostic testing metadata consumed by code generator (Module 8)."""

    component: str = Field(..., description="Name of the component containing the element.")
    element: str = Field(..., description="Descriptive element identifier under test.")
    element_type: str = Field(..., description="Type of DOM or abstract element: button, textbox, form, etc.")
    locator: TestCaseLocator = Field(..., description="Locator parameters to query the element.")
    action: str = Field(..., description="Interation action: click, type, select, submit, navigate, render, state_update, audit, etc.")
    assertion_type: str = Field(..., description="Expectation category: exists, validation, callback_triggered, state_value, http_status, error_thrown, route_change, accessibility_standard.")
    assertion_target: str = Field(..., description="Target node or object of assertion validation.")
    expected_value: Any = Field(None, description="Deterministic expected assertion comparison value (accepts string, int, float, bool, list, dict, or null).")
    mock_required: bool = Field(False, description="True if mock services are required.")
    mock_services: List[str] = Field(default_factory=list, description="List of dependency mock service injections.")
    pre_test_state: Dict[str, Any] = Field(default_factory=dict, description="Initial component states.")
    post_test_state: Dict[str, Any] = Field(default_factory=dict, description="Post-execution expected component states.")
    dependencies: List[str] = Field(default_factory=list, description="Injectable class or router dependency references.")
    accessibility_checks: List[str] = Field(default_factory=list, description="Specific WCAG auditing checklists.")
    cleanup_actions: List[str] = Field(default_factory=list, description="Teardown methods to run post-test.")


class TestCaseStep(BaseModel):
    """Structured representation of a single human-readable test step."""

    action: str = Field(..., description="Human-readable action description.")
    expected: str = Field(..., description="Observable expected outcome.")


class TestCaseTraceability(BaseModel):
    """Technical traceability references."""

    strategy_id: str = Field(..., description="Reference to the parent test strategy ID.")
    edge_case_id: str = Field(..., description="Reference to the parent edge case ID.")
    component_id: str = Field(..., description="Reference to Component ID.")
    project_id: Optional[str] = Field(None, description="Unique project identifier.")
    pipeline_run_id: Optional[str] = Field(None, description="Unique pipeline run identifier.")
    source_file: Optional[str] = Field(None, description="Relative path to component source file.")
    element_id: Optional[str] = Field(None, description="Stable target UIElement ID.")
    event_id: Optional[str] = Field(None, description="Stable target event ID.")
    state_id: Optional[str] = Field(None, description="Stable target state ID.")
    service_id: Optional[str] = Field(None, description="Stable target service ID.")
    route_id: Optional[str] = Field(None, description="Stable target route ID.")
    
    # ---- Human-Readable Traceability Aliases ----
    component: Optional[str] = Field(None, description="Name of the component.")
    function: Optional[str] = Field(None, description="Target function or handler name.")
    strategy: Optional[str] = Field(None, description="Strategy objective description.")
    edge_case: Optional[str] = Field(None, description="Edge case scenario title.")


class TestCase(BaseModel):
    """Structured representation of a framework-agnostic test case."""

    id: str = Field(..., description="Unique test case identifier (e.g. 'TC-STRAT-EVENT-001-RAPID-CLICKS').")
    strategy_id: str = Field(..., description="Reference to the parent test strategy ID.")
    edge_case_id: str = Field(..., description="Reference to the parent edge case ID.")
    category: str = Field(..., description="Test case category (Forms, Events, State, Services, Routing, Accessibility).")
    priority: str = Field(..., description="Priority level: High, Medium, Low.")
    component: str = Field(..., description="Target component or system under test.")
    title: str = Field(..., description="Descriptive title of the test case.")
    objective: str = Field(..., description="Clear testing objective.")
    preconditions: List[str] = Field(default_factory=list, description="List of prerequisites before running the test.")
    steps: List[Union[TestCaseStep, str]] = Field(default_factory=list, description="Step-by-step test execution path.")
    test_data: Dict[str, Any] = Field(default_factory=dict, description="Test input data inputs.")
    expected_result: str = Field(..., description="Deterministic expected result verification criteria.")
    tags: List[str] = Field(default_factory=list, description="Metadata tags for categorization.")
    metadata: TestCaseMetadata = Field(..., description="Enriched framework-agnostic testing metadata block.")
    traceability: Optional[TestCaseTraceability] = None

    # ---- Human-Readable Specification & Function Fields ----
    component_specification: Optional[str] = Field(None, description="High-level human readable specification of component purpose.")
    target_function: Optional[str] = Field(None, description="Specific target function/method/handler name (e.g. 'handleSubmit()').")
    why_this_test_matters: Optional[str] = Field(None, description="Rationale explaining business or technical risk of this test.")

    # ---- Traceability References ----
    project_id: Optional[str] = Field(None, description="Unique project identifier.")
    pipeline_run_id: Optional[str] = Field(None, description="Unique pipeline run identifier.")
    source_file: Optional[str] = Field(None, description="Relative path to component source file.")
    component_id: Optional[str] = Field(None, description="Stable target component ID.")
    element_id: Optional[str] = Field(None, description="Stable target UIElement ID.")
    event_id: Optional[str] = Field(None, description="Stable target event ID.")
    state_id: Optional[str] = Field(None, description="Stable target state ID.")
    service_id: Optional[str] = Field(None, description="Stable target service ID.")
    route_id: Optional[str] = Field(None, description="Stable target route ID.")

    # ---- Behavioral User Workflow Enriched Fields (v3) ----
    risk: Optional[str] = Field(None, description="Risk level and score (e.g. 'Low (2/10)').")
    mock_requirements: List[str] = Field(default_factory=list, description="Mock specifications.")
    expected_dom_changes: List[str] = Field(default_factory=list, description="DOM side effects.")
    expected_state_changes: Dict[str, Any] = Field(default_factory=dict, description="State side effects.")
    expected_accessibility_behavior: Optional[str] = Field(None, description="Accessibility behavior verification.")
    expected_side_effects: List[str] = Field(default_factory=list, description="Side effects (network, storage, router).")
    test_quality_score: Optional[int] = Field(None, description="Quality validation score (0-100).")

    @field_validator("id", "strategy_id", "edge_case_id", "category", "priority", "component", "title", "objective", "expected_result")
    @classmethod
    def validate_non_empty_strings(cls, value: str, info: Any) -> str:
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{info.field_name} must be a non-empty string.")
        return value

    @field_validator("priority")
    @classmethod
    def validate_priority(cls, value: str) -> str:
        valid_priorities = {"high", "medium", "low"}
        if value.lower() not in valid_priorities:
            raise ValueError(f"Invalid priority: {value}. Must be one of High, Medium, Low.")
        return value


# TestCasePlanRequest directly accepts StrategyPlanResponse without a wrapper.
TestCasePlanRequest = StrategyPlanResponse


class TestCasePlanResponse(BaseModel):
    """Response payload containing generated structured test cases."""

    project_name: str = Field(..., description="Name of the project.")
    project_id: Optional[str] = Field(None, description="Unique project identifier.")
    pipeline_run_id: Optional[str] = Field(None, description="Unique pipeline run identifier.")
    framework: str = Field(..., description="Original framework name.")
    total_test_cases: int = Field(0, ge=0, description="Total test cases generated.")
    test_cases: List[TestCase] = Field(default_factory=list, description="List of generated test cases.")
    coverage_summary: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Summary of components, functions, and behaviors covered.")
