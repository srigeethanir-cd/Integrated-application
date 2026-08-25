"""
Test Strategy Models – Module 5.

Defines Pydantic schemas for representing framework-agnostic test strategies
generated from the Intermediate Representation (IR).
"""

from __future__ import annotations

from typing import List, Optional
from pydantic import BaseModel, Field


class TestStrategy(BaseModel):
    """A single framework-agnostic test strategy specification."""

    id: str = Field(..., description="Unique strategy identifier (e.g. 'STRAT-LOGIN-001').")
    category: str = Field(
        ...,
        description=(
            "Strategy category: 'Rendering Tests', 'Component Initialization', "
            "'User Interaction Tests', 'Event Handling Tests', 'Form Validation Tests', "
            "'State Management Tests', 'API/Service Interaction Tests', 'Routing Tests', "
            "'Conditional Rendering Tests', 'Error Handling Tests', 'Accessibility Tests'."
        ),
    )
    priority: str = Field(
        ..., description="Priority level: 'High', 'Medium', 'Low'."
    )
    target_component: str = Field(..., description="Target component or element identifier.")
    description: str = Field(..., description="High-level description of what should be tested and why.")
    preconditions: List[str] = Field(
        default_factory=list, description="Preconditions required before executing the test."
    )
    coverage_tags: List[str] = Field(
        default_factory=list, description="Coverage tags (e.g. ['render', 'props', 'state', 'a11y'])."
    )
    is_covered: bool = Field(
        False, description="True if an existing test file already covers this strategy."
    )

    # ---- Traceability Enriched Fields (v2) ----
    strategy_id: Optional[str] = Field(None, description="Unique strategy identifier (traceability).")
    project_id: Optional[str] = Field(None, description="Unique project identifier.")
    pipeline_run_id: Optional[str] = Field(None, description="Unique pipeline run identifier.")
    source_file: Optional[str] = Field(None, description="Relative path to component source file.")
    component: Optional[str] = Field(None, description="Target component name.")
    target_function: Optional[str] = Field(None, description="Target function or handler name (e.g. handleSubmit()).")
    component_id: Optional[str] = Field(None, description="ID of the target component (traceability).")
    element_id: Optional[str] = Field(None, description="ID of the target element (traceability).")
    event_id: Optional[str] = Field(None, description="ID of the target event (traceability).")
    state_id: Optional[str] = Field(None, description="ID of the target state (traceability).")
    service_id: Optional[str] = Field(None, description="ID of the target service (traceability).")
    route_id: Optional[str] = Field(None, description="ID of the target route (traceability).")

    # ---- Behavior-Driven Strategy Enriched Fields (v3) ----
    risk: Optional[str] = Field(None, description="Risk level and score (e.g. 'Low (2/10)').")
    reason: Optional[str] = Field(None, description="Risk and strategy justification reason.")
    behavior_reference: Optional[str] = Field(None, description="Reference to IR interaction or state transition.")
    expected_outcome: Optional[str] = Field(None, description="Behavior-driven expected outcome description.")
    test_objective: Optional[str] = Field(None, description="Specific testing objective derived from IR.")


class StrategyPlanResponse(BaseModel):
    """Top-level strategy plan response returned by Module 5."""

    project_name: str = Field(..., description="Name of the project.")
    project_id: Optional[str] = Field(None, description="Unique project identifier.")
    pipeline_run_id: Optional[str] = Field(None, description="Unique pipeline run identifier.")
    framework: str = Field(..., description="Original framework name.")
    total_strategies: int = Field(0, ge=0, description="Total strategies generated.")
    covered_strategies_count: int = Field(0, ge=0, description="Strategies already covered by existing tests.")
    uncovered_strategies_count: int = Field(0, ge=0, description="Strategies requiring new test generation.")
    strategies: List[TestStrategy] = Field(default_factory=list, description="List of generated test strategies.")
