"""
Edge Case Models – Module 6.

Defines Pydantic schemas for framework-agnostic edge case scenarios
mapped to test strategies.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from app.models.ir_models import FrameworkAgnosticIR
from app.models.strategy_models import StrategyPlanResponse


class EdgeCasePlanRequest(BaseModel):
    """Payload to trigger Edge Case Scenario generation."""

    ir: Optional[FrameworkAgnosticIR] = Field(None, description="Framework-Agnostic IR from Module 4.")
    strategy_plan: StrategyPlanResponse = Field(..., description="Generated Strategy Plan from Module 5.")


class EdgeCaseScenario(BaseModel):
    """A framework-agnostic edge case scenario mapped to a test strategy."""

    id: str = Field(..., description="Unique edge case identifier (e.g. 'EC-LOGIN-INIT-001').")
    strategy_id: str = Field(..., description="Reference to the parent test strategy ID.")
    category: str = Field(
        ...,
        description="Edge case category (e.g. 'Forms', 'Events', 'State', 'Services', 'Routing', 'Accessibility').",
    )
    priority: str = Field(..., description="Priority level: 'High', 'Medium', 'Low'.")
    title: str = Field(..., description="Short title of the edge case scenario.")
    description: str = Field(..., description="Detailed description of the test scenario.")
    input_data: Dict[str, Any] = Field(
        default_factory=dict, description="Test input data (payload, keys pressed, route params, etc.)."
    )
    expected_behavior: str = Field(..., description="Expected behavior or assertion goal.")
    tags: List[str] = Field(default_factory=list, description="Descriptive metadata tags.")

    # ---- Traceability Enriched Fields (v2) ----
    project_id: Optional[str] = Field(None, description="Unique project identifier.")
    pipeline_run_id: Optional[str] = Field(None, description="Unique pipeline run identifier.")
    source_file: Optional[str] = Field(None, description="Relative path to component source file.")
    target_function: Optional[str] = Field(None, description="Target function or handler name (e.g. handleSubmit()).")
    component_id: Optional[str] = Field(None, description="Stable target component ID.")
    element_id: Optional[str] = Field(None, description="Stable target UIElement ID.")
    event_id: Optional[str] = Field(None, description="Stable target event ID.")
    state_id: Optional[str] = Field(None, description="Stable target state ID.")
    service_id: Optional[str] = Field(None, description="Stable target service ID.")
    route_id: Optional[str] = Field(None, description="Stable target route ID.")

    # ---- Testing Metadata Enriched Fields (v2) ----
    edge_case_type: Optional[str] = Field(None, description="Sub-type classification of edge case.")
    assertions: List[str] = Field(default_factory=list, description="Assert statements list.")
    locator_rtl: Optional[str] = Field(None, description="RTL locator hint.")
    locator_angular: Optional[str] = Field(None, description="Angular locator hint.")
    jest_matcher: Optional[str] = Field(None, description="Jest matcher (toBeInTheDocument, toHaveBeenCalled).")
    mock_requirements: List[str] = Field(default_factory=list, description="Mock specifications.")
    expected_state_changes: Dict[str, Any] = Field(default_factory=dict, description="State side effects.")
    expected_dom_changes: List[str] = Field(default_factory=list, description="DOM side effects.")

    # ---- Behavioral Explanations (v3) ----
    why_it_exists: Optional[str] = Field(None, description="Explanation of why this edge case exists based on component behavior.")
    what_behavior_it_validates: Optional[str] = Field(None, description="Specific behavior validated.")
    what_failure_it_prevents: Optional[str] = Field(None, description="Concrete failure or regression prevented.")


class EdgeCasePlanResponse(BaseModel):
    """Top-level edge case plan response returned by Module 6."""

    project_name: str = Field(..., description="Name of the project.")
    project_id: Optional[str] = Field(None, description="Unique project identifier.")
    pipeline_run_id: Optional[str] = Field(None, description="Unique pipeline run identifier.")
    framework: str = Field(..., description="Original framework name.")
    total_edge_cases: int = Field(0, ge=0, description="Total edge cases generated.")
    edge_cases: List[EdgeCaseScenario] = Field(
        default_factory=list, description="List of mapped edge case scenarios."
    )
