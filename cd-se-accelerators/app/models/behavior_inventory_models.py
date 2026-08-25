"""
Behavior Inventory Models – Intermediate representation for Frontend Analysis.

Defines structured Pydantic models for deep source code analysis of components and custom hooks,
capturing state variables, function behaviors, state transitions, event handlers, API calls,
validations, and hooks.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field, field_validator


class StateBehaviorItem(BaseModel):
    """Represents a state variable declared within a component or hook."""

    name: str = Field(..., description="Name of the state variable (e.g. 'email', 'rememberMe').")
    initial_value: Optional[str] = Field(None, description="Initial value or code expression (e.g. '\"\"', 'false', '0', '[]').")
    type: str = Field("unknown", description="Inferred state type (e.g. 'string', 'boolean', 'number', 'array', 'object').")
    setter_name: Optional[str] = Field(None, description="Associated setter function name if React state (e.g. 'setEmail').")


class FunctionBehaviorItem(BaseModel):
    """Represents a function, method, or event handler defined in a component/hook."""

    name: str = Field(..., description="Name of the function or handler (e.g. 'handleSubmit', 'handleEmailChange').")
    behavior: str = Field(..., description="Behavior summary (e.g. 'updates email state from event.target.value').")
    inputs: List[str] = Field(default_factory=list, description="Parameters or event object inputs (e.g. ['event']).")
    outputs: str = Field("void", description="Return value or type.")
    state_modified: List[str] = Field(default_factory=list, description="State variables modified by this function (e.g. ['email']).")
    state_not_modified: List[str] = Field(default_factory=list, description="State variables not touched by this function.")
    events_consumed: List[str] = Field(default_factory=list, description="DOM or custom events handled (e.g. ['submit', 'change']).")
    conditions: List[str] = Field(default_factory=list, description="Conditional checks inside function.")
    side_effects: List[str] = Field(default_factory=list, description="Side effects (e.g. 'e.preventDefault()', 'navigate()').")
    dependencies: List[str] = Field(default_factory=list, description="Services, hooks, or utils referenced.")
    success_path: Optional[str] = Field(None, description="Expected behavior on clean execution.")
    failure_path: Optional[str] = Field(None, description="Expected behavior on error / validation failure.")


class StateTransitionItem(BaseModel):
    """Represents a state transition mapping from initial state to resulting state via a function."""

    initial_state: str = Field(..., description="Initial state condition (e.g. 'email = \"\"').")
    triggering_function: str = Field(..., description="Function call triggering transition (e.g. 'handleEmailChange(\"user@test.com\")').")
    state_transition: str = Field(..., description="Setter call or code execution (e.g. 'setEmail(\"user@test.com\")').")
    resulting_state: str = Field(..., description="Resulting state condition (e.g. 'email = \"user@test.com\"').")


class PropBehaviorItem(BaseModel):
    """Represents a prop or component input."""

    name: str = Field(..., description="Prop or Input name.")
    type: str = Field("any", description="Prop type annotation.")
    default_value: Optional[str] = Field(None, description="Default value if provided.")
    required: bool = Field(False, description="True if required prop.")


class ValidationBehaviorItem(BaseModel):
    """Represents a form or field validation rule found in code."""

    field: str = Field(..., description="Target field name under validation.")
    rule: str = Field(..., description="Validation rule description (e.g. 'required', 'email_format', 'min_length').")
    error_message: Optional[str] = Field(None, description="User-facing error message.")
    condition: Optional[str] = Field(None, description="Code condition enforcing validation.")


class ApiCallBehaviorItem(BaseModel):
    """Represents an HTTP service or API call detected in component/hook."""

    endpoint: str = Field(..., description="API endpoint URL pattern or method call.")
    http_method: Optional[str] = Field("GET", description="HTTP verb (GET, POST, PUT, DELETE).")
    is_async: bool = Field(True, description="True if async/await or Promise based.")
    has_error_handling: bool = Field(False, description="True if inside try/catch or .catch() chain.")
    in_use_effect: bool = Field(False, description="True if executed automatically inside useEffect / ngOnInit.")


class ConditionBehaviorItem(BaseModel):
    """Represents a conditional rendering or branch check in component/hook."""

    expression: str = Field(..., description="Guard expression or ternary condition.")
    true_branch: Optional[str] = Field(None, description="Target render or behavior if true.")
    false_branch: Optional[str] = Field(None, description="Target render or behavior if false.")


class ComponentBehaviorInventory(BaseModel):
    """Structured behavior inventory for a single React/Angular component or hook."""

    component: str = Field(..., description="Component or hook name (e.g. 'useLoginForm', 'LoginCard').")
    source_file: str = Field(..., description="Relative or absolute path to source file.")
    component_type: str = Field("component", description="Identifier type: 'component', 'hook', 'service'.")
    states: List[StateBehaviorItem] = Field(default_factory=list, description="State variables.")
    functions: List[FunctionBehaviorItem] = Field(default_factory=list, description="Functions and handlers.")
    hooks: List[str] = Field(default_factory=list, description="List of React/Angular hooks used.")
    props: List[PropBehaviorItem] = Field(default_factory=list, description="Props or component inputs.")
    event_handlers: List[str] = Field(default_factory=list, description="Names of event handler functions.")
    validations: List[ValidationBehaviorItem] = Field(default_factory=list, description="Validation rules.")
    api_calls: List[ApiCallBehaviorItem] = Field(default_factory=list, description="API / service calls.")
    conditions: List[ConditionBehaviorItem] = Field(default_factory=list, description="Branch conditions.")
    state_transitions: List[StateTransitionItem] = Field(default_factory=list, description="State transition maps.")


class BehaviorInventoryResponse(BaseModel):
    """Top-level response model containing the full Frontend Behavior Inventory."""

    project_name: str = Field(..., description="Name of the project under analysis.")
    project_id: Optional[str] = Field(None, description="Unique project identifier.")
    pipeline_run_id: Optional[str] = Field(None, description="Unique pipeline run identifier.")
    framework: str = Field(..., description="Framework name (React, Next.js, Angular).")
    total_components: int = Field(0, ge=0, description="Total components/hooks in inventory.")
    total_functions: int = Field(0, ge=0, description="Total functions discovered.")
    total_states: int = Field(0, ge=0, description="Total state variables discovered.")
    total_hooks: int = Field(0, ge=0, description="Total hook occurrences discovered.")
    total_handlers: int = Field(0, ge=0, description="Total event handlers discovered.")
    total_api_calls: int = Field(0, ge=0, description="Total API calls discovered.")
    total_validations: int = Field(0, ge=0, description="Total validations discovered.")
    inventory: List[ComponentBehaviorInventory] = Field(default_factory=list, description="List of component behavior inventories.")
