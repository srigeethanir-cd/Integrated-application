"""
Frontend Context Extraction Engine (FCE) Data Models.

Defines Pydantic models for implementation-level ground truth extracted from source code.
"""

from __future__ import annotations
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class PropContextItem(BaseModel):
    """Extracted component prop or Angular @Input binding."""
    name: str = Field(..., description="Prop or input property name.")
    type: str = Field("any", description="Inferred or declared prop data type.")
    default_value: Optional[str] = Field(None, description="Default value if specified.")
    required: bool = Field(False, description="True if prop is required.")


class StateContextItem(BaseModel):
    """Extracted React state or Angular property."""
    name: str = Field(..., description="State variable or property name.")
    initial_value: Optional[str] = Field(None, description="Initial state value as source text.")
    setter: Optional[str] = Field(None, description="Setter function name (e.g. setEmail).")
    state_type: str = Field("unknown", description="Data type of the state variable.")
    management_type: str = Field("useState", description="State mechanism (useState, useReducer, property).")


class HookContextItem(BaseModel):
    """Extracted hook invocation."""
    name: str = Field(..., description="Hook name (useState, useEffect, custom hook).")
    dependencies: List[str] = Field(default_factory=list, description="Dependency array references.")
    is_custom: bool = Field(False, description="True if custom hook.")
    params: List[str] = Field(default_factory=list, description="Hook call parameters.")
    return_values: List[str] = Field(default_factory=list, description="Destructured return variables.")


class FunctionContextItem(BaseModel):
    """Extracted function or method implementation."""
    name: str = Field(..., description="Function or method identifier.")
    parameters: List[str] = Field(default_factory=list, description="Function argument names.")
    reads: List[str] = Field(default_factory=list, description="State or event properties read (e.g. event.target.value).")
    writes: List[str] = Field(default_factory=list, description="State variables mutated (e.g. email).")
    behavior: str = Field("", description="Explicit action description.")
    return_type: str = Field("void", description="Inferred return type.")
    is_async: bool = Field(False, description="True if async or returning Promise.")


class EventContextItem(BaseModel):
    """Extracted JSX or template event binding."""
    name: str = Field(..., description="Event binding (onChange, onSubmit, (click)).")
    handler: str = Field(..., description="Invoked function or method name.")
    element_tag: str = Field("div", description="JSX or HTML tag name.")
    prevent_default: bool = Field(False, description="True if preventDefault is invoked.")
    stop_propagation: bool = Field(False, description="True if stopPropagation is invoked.")


class ConditionContextItem(BaseModel):
    """Extracted conditional rendering or branch."""
    condition: str = Field(..., description="Condition expression.")
    type: str = Field("ternary", description="Branch type: ternary, logical_and, if_statement.")
    dependent_state: List[str] = Field(default_factory=list, description="State variables driving condition.")
    rendered_ui: List[str] = Field(default_factory=list, description="Elements or components conditionally rendered.")


class ApiCallContextItem(BaseModel):
    """Extracted HTTP service or API call."""
    function_name: str = Field("fetch", description="Invoked API function name.")
    endpoint: Optional[str] = Field(None, description="API endpoint URL pattern.")
    http_method: str = Field("GET", description="HTTP verb (GET, POST, PUT, DELETE).")
    is_async: bool = Field(True, description="True if async/Promise based.")
    has_error_handling: bool = Field(False, description="True if inside try/catch or .catch() chain.")
    in_use_effect: bool = Field(False, description="True if executed in useEffect/ngOnInit.")
    loading_state_var: Optional[str] = Field(None, description="Associated loading state variable if any.")


class ValidationContextItem(BaseModel):
    """Extracted form validation rule."""
    field: str = Field(..., description="Target form control field.")
    rule: str = Field(..., description="Validation constraint description.")
    error_message: Optional[str] = Field(None, description="Associated validation error message.")


class SideEffectContextItem(BaseModel):
    """Extracted side effect or external interaction."""
    trigger: str = Field(..., description="Triggering event or hook.")
    effect: str = Field(..., description="Side effect description.")


class ChildComponentContextItem(BaseModel):
    """Extracted child component reference."""
    name: str = Field(..., description="Child component tag name.")
    props_passed: List[str] = Field(default_factory=list, description="Prop names passed to child.")


class BehaviorMappingItem(BaseModel):
    """Explicit mapping from code trigger to state/effect."""
    behavior_id: str = Field(..., description="Unique behavior ID.")
    component_id: str = Field(..., description="Target component ID.")
    function: str = Field(..., description="Function or handler name.")
    trigger: str = Field(..., description="Trigger event.")
    input: str = Field(..., description="Input expression read.")
    state_change: str = Field(..., description="State variable modified.")
    expected_effect: str = Field(..., description="Resulting effect description.")


class StateTransitionItem(BaseModel):
    """State transition sequence: initial -> trigger -> handler -> state update -> resulting state."""
    initial_state: str = Field(..., description="Starting state description.")
    triggering_function: str = Field(..., description="Handler or trigger name.")
    state_transition: str = Field(..., description="State setter call.")
    resulting_state: str = Field(..., description="New state description.")


class CompletenessReport(BaseModel):
    """Completeness metrics for static context extraction."""
    components_discovered: int = Field(0, description="Total components discovered.")
    components_analyzed: int = Field(0, description="Total components successfully analyzed.")
    functions_discovered: int = Field(0, description="Total functions/methods extracted.")
    states_discovered: int = Field(0, description="Total state variables extracted.")
    hooks_discovered: int = Field(0, description="Total hooks extracted.")
    handlers_discovered: int = Field(0, description="Total event handlers extracted.")
    api_calls_discovered: int = Field(0, description="Total API calls extracted.")
    validations_discovered: int = Field(0, description="Total form validations extracted.")
    incomplete_contexts: List[str] = Field(default_factory=list, description="Component IDs with partial context warnings.")


class SingleComponentFrontendContext(BaseModel):
    """Complete, structured context extracted for a single component or hook."""
    project_id: Optional[str] = Field(None, description="Unique project ID.")
    pipeline_run_id: Optional[str] = Field(None, description="Unique pipeline run ID.")
    component_id: str = Field(..., description="Component identifier.")
    component_name: str = Field(..., description="Component or hook name.")
    source_file: str = Field(..., description="Relative path to component source file.")
    framework: str = Field("React", description="Frontend framework (React, Angular, Next.js).")

    props: List[PropContextItem] = Field(default_factory=list, description="Props or @Input bindings.")
    states: List[StateContextItem] = Field(default_factory=list, description="State variables.")
    hooks: List[HookContextItem] = Field(default_factory=list, description="Hooks invoked.")
    functions: List[FunctionContextItem] = Field(default_factory=list, description="Functions or methods.")
    events: List[EventContextItem] = Field(default_factory=list, description="JSX/template event bindings.")
    conditions: List[ConditionContextItem] = Field(default_factory=list, description="Conditional rendering rules.")
    api_calls: List[ApiCallContextItem] = Field(default_factory=list, description="HTTP/API service calls.")
    validations: List[ValidationContextItem] = Field(default_factory=list, description="Form validations.")
    side_effects: List[SideEffectContextItem] = Field(default_factory=list, description="Side effects.")
    child_components: List[ChildComponentContextItem] = Field(default_factory=list, description="Child component usages.")
    dependencies: List[str] = Field(default_factory=list, description="Component dependencies.")
    behaviors: List[BehaviorMappingItem] = Field(default_factory=list, description="Explicit behavior mappings.")
    state_transitions: List[StateTransitionItem] = Field(default_factory=list, description="State transitions.")


class FrontendContextResponse(BaseModel):
    """Aggregate payload returned by Frontend Context Extraction Engine."""
    project_name: str = Field("Project", description="Project name.")
    project_id: Optional[str] = Field(None, description="Project ID.")
    pipeline_run_id: Optional[str] = Field(None, description="Pipeline run ID.")
    framework: str = Field("React", description="Framework name.")
    contexts: List[SingleComponentFrontendContext] = Field(default_factory=list, description="Extracted component contexts.")
    completeness_report: CompletenessReport = Field(default_factory=CompletenessReport, description="Completeness metrics.")
