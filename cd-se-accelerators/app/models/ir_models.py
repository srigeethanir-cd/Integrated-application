"""
Framework-Agnostic Intermediate Representation (IR) Models – Module 4.

Defines the normalized schema for representing components, UI elements,
events, state, forms, services, routes, dependencies, and existing tests
in a framework-independent manner.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

# Import enriched models from Project Analyzer (Module 3) to prevent duplication
from app.models.analyzer_models import (
    AccessibilityInfo,
    TestingMetadata,
    DependencyNode,
    TestMapping,
    ComponentRelationshipInfo,
)


class UIElement(BaseModel):
    """Normalized UI Element (JSX element or Angular template binding)."""

    tag: str = Field(..., description="Element HTML tag or component selector.")
    component_name: str = Field(..., description="Name of the enclosing component.")
    attributes: List[str] = Field(default_factory=list, description="Attribute or property binding names.")
    children_count: int = Field(0, ge=0, description="Direct children element count.")

    # ---- Enriched fields (v2) ----
    id: Optional[str] = Field(None, description="Stable element ID.")
    class_name: Optional[str] = Field(None, description="CSS class name.")
    role: Optional[str] = Field(None, description="ARIA role attribute.")
    aria_label: Optional[str] = Field(None, description="aria-label attribute value.")
    aria_expanded: Optional[str] = Field(None, description="aria-expanded attribute value.")
    placeholder: Optional[str] = Field(None, description="placeholder attribute value.")
    alt: Optional[str] = Field(None, description="alt attribute value.")
    disabled: Optional[str] = Field(None, description="disabled attribute value.")
    required: Optional[str] = Field(None, description="required attribute value.")
    value_binding: Optional[str] = Field(None, description="Value binding source text.")
    event_bindings: List[Dict[str, str]] = Field(default_factory=list, description="Event mappings.")
    locator_rtl: Optional[str] = Field(None, description="React Testing Library preferred locator.")
    locator_angular: Optional[str] = Field(None, description="Angular TestBed preferred locator.")
    locator_fallback: Optional[str] = Field(None, description="Fallback element locator.")
    assertion_hints: List[str] = Field(default_factory=list, description="Recommended assertion keys.")


class UIEvent(BaseModel):
    """Normalized UI Event (e.g. onClick, onChange, (click), (ngSubmit))."""

    name: str = Field(..., description="Event binding name.")
    event_type: str = Field(..., description="Normalized event type (click, change, submit, etc.).")
    component_name: str = Field(..., description="Enclosing component name.")
    handler_name: str = Field(..., description="Associated handler or method name.")

    # ---- Enriched fields (v2) ----
    id: Optional[str] = Field(None, description="Stable event ID.")
    target_element_id: Optional[str] = Field(None, description="ID of the target UIElement.")
    updates_states: List[str] = Field(default_factory=list, description="IDs of states updated by this event.")
    service_calls: List[str] = Field(default_factory=list, description="Service functions invoked.")
    navigation: bool = Field(False, description="True if handler navigates.")
    prevent_default: bool = Field(False, description="True if handler prevents default behavior.")
    stop_propagation: bool = Field(False, description="True if handler stops propagation.")
    assertion_hints: List[str] = Field(default_factory=list, description="Assertion suggestions.")


class ComponentState(BaseModel):
    """Normalized state representation (React useState, class state, component properties)."""

    name: str = Field(..., description="State property or variable name.")
    component_name: str = Field(..., description="Enclosing component name.")
    type: str = Field("state", description="Kind of state: 'state', 'local', 'hook'.")
    initial_value: Optional[str] = Field(None, description="Initial value as source text.")
    setter: Optional[str] = Field(None, description="Setter function name if applicable.")

    # ---- Enriched fields (v2) ----
    id: Optional[str] = Field(None, description="Stable state ID.")
    state_type: str = Field("unknown", description="Inferred type of state.")
    used_by_elements: List[str] = Field(default_factory=list, description="IDs of elements using this state.")
    updated_by_events: List[str] = Field(default_factory=list, description="IDs of events updating this state.")


class FormField(BaseModel):
    """Normalized form control field."""

    name: str = Field(..., description="Control or field name.")
    type: str = Field("control", description="Field type: 'control', 'input', 'group'.")
    validators: List[str] = Field(default_factory=list, description="Associated validators.")

    # ---- Enriched fields (v2) ----
    id: Optional[str] = Field(None, description="Stable field ID.")
    is_controlled: bool = Field(False, description="True if field is controlled.")
    is_required: bool = Field(False, description="True if field is required.")
    validation_rules: List[str] = Field(default_factory=list, description="Rules list.")


class FormModel(BaseModel):
    """Normalized form representation (Angular Reactive Form, React form state)."""

    name: str = Field(..., description="Form identifier or variable name.")
    component_name: str = Field(..., description="Enclosing component name.")
    controls: List[FormField] = Field(default_factory=list, description="Form controls.")
    validators: List[str] = Field(default_factory=list, description="Form-level validators.")

    # ---- Enriched fields (v2) ----
    id: Optional[str] = Field(None, description="Stable form ID.")
    element: str = Field("form", description="Root element tag.")
    is_controlled: bool = Field(False, description="True if form is controlled.")
    submit_handler: Optional[str] = Field(None, description="onSubmit handler function.")
    reset_handler: Optional[str] = Field(None, description="onReset handler function.")
    library: Optional[str] = Field(None, description="Form library used.")


class ServiceDependency(BaseModel):
    """Normalized service dependency or external API call."""

    name: str = Field(..., description="Service or API function name.")
    component_name: Optional[str] = Field(None, description="Enclosing component name.")
    type: str = Field(..., description="Dependency type: 'http', 'service_call', 'injected_service', 'fetch', 'axios'.")
    methods: List[str] = Field(default_factory=list, description="Invoked service methods.")

    # ---- Enriched fields (v2) ----
    id: Optional[str] = Field(None, description="Stable service dependency ID.")
    api_calls: List[Dict[str, Any]] = Field(default_factory=list, description="Associated API calls.")


class RouteModel(BaseModel):
    """Normalized route definition."""

    path: str = Field(..., description="Route URL path.")
    component: Optional[str] = Field(None, description="Target component name.")
    guard: Optional[str] = Field(None, description="Route guard name if specified.")
    lazy_loaded: bool = Field(False, description="True if route is lazy-loaded.")

    # ---- Enriched fields (v2) ----
    id: Optional[str] = Field(None, description="Stable route ID.")
    redirects: List[str] = Field(default_factory=list, description="Redirect targets.")
    route_params: List[str] = Field(default_factory=list, description="URL parameters.")


class HookInfo(BaseModel):
    """Detailed hook analysis representation."""

    name: str = Field(..., description="Hook name (useState, useEffect, useMemo, useContext, custom hook).")
    purpose: str = Field(..., description="Purpose or responsibility of the hook.")
    dependencies: List[str] = Field(default_factory=list, description="Hook dependency array references.")
    cleanup: bool = Field(False, description="True if hook registers teardown or cleanup callback.")
    side_effects: List[str] = Field(default_factory=list, description="List of identified side effects.")


class InteractionGraphNode(BaseModel):
    """Interaction flow step: User Action -> Event -> Handler -> State Update -> DOM Change -> Business Effect."""

    user_action: str = Field(..., description="Triggering user interaction.")
    event: str = Field(..., description="Triggered event binding.")
    handler: str = Field(..., description="Invoked handler function name.")
    state_update: Optional[str] = Field(None, description="Component state mutated by handler.")
    dom_change: Optional[str] = Field(None, description="DOM element or component toggled/updated.")
    business_effect: Optional[str] = Field(None, description="High-level business effect.")


class StateTransition(BaseModel):
    """State transition graph step."""

    current_state: str = Field(..., description="Starting state status or value.")
    trigger: str = Field(..., description="Event or user trigger.")
    next_state: str = Field(..., description="Destination state status or value.")
    affected_elements: List[str] = Field(default_factory=list, description="Elements or components affected by state transition.")


class RenderCondition(BaseModel):
    """Conditional rendering branch details."""

    condition: str = Field(..., description="JSX or template conditional condition string.")
    dependent_state: List[str] = Field(default_factory=list, description="State or prop variables driving condition.")
    affected_ui: List[str] = Field(default_factory=list, description="UI elements or components conditionally rendered.")
    visibility_rule: str = Field(..., description="Visibility outcome rule.")


class DataFlowInfo(BaseModel):
    """Data flow tracking: Props -> State -> Derived values -> Rendered output -> Child props."""

    props_to_state: List[Dict[str, str]] = Field(default_factory=list, description="Props copied into state.")
    state_to_derived: List[Dict[str, str]] = Field(default_factory=list, description="Derived state or memoized computations.")
    prop_drilling: List[str] = Field(default_factory=list, description="Props forwarded to child components.")
    context_used: List[str] = Field(default_factory=list, description="React Contexts or stores consumed.")
    api_response_used: List[str] = Field(default_factory=list, description="API service responses populating state.")
    memoized_values: List[str] = Field(default_factory=list, description="useMemo or useCallback items.")


class AccessibilityDetail(BaseModel):
    """Comprehensive WCAG accessibility evaluation."""

    aria_roles: List[str] = Field(default_factory=list, description="Declared ARIA roles.")
    labels: List[str] = Field(default_factory=list, description="Associated aria-labels or HTML labels.")
    keyboard_navigation: List[str] = Field(default_factory=list, description="Keyboard events handled.")
    focus_management: Optional[str] = Field(None, description="Focus trap or focus management details.")
    tab_order: Optional[str] = Field(None, description="TabIndex or tab order details.")
    alt_text: List[str] = Field(default_factory=list, description="Image alt attributes.")
    missing_accessibility: List[str] = Field(default_factory=list, description="Missing accessibility attributes or warnings.")


class RiskAnalysis(BaseModel):
    """Dynamic weighted risk calculation."""

    score: int = Field(1, ge=1, le=10, description="Dynamically calculated risk score (1-10).")
    level: str = Field("Low", description="Risk level: Low (1-3), Medium (4-6), High (7-10).")
    risk_reasons: List[str] = Field(default_factory=list, description="Explanations for calculated risk score.")


class ComponentTestability(BaseModel):
    """Component testability metadata and recommendations."""

    rendering: List[str] = Field(default_factory=list, description="Rendering assertion targets.")
    state: List[str] = Field(default_factory=list, description="State transition verification targets.")
    props: List[str] = Field(default_factory=list, description="Props validation targets.")
    events: List[str] = Field(default_factory=list, description="Event handler test targets.")
    accessibility: List[str] = Field(default_factory=list, description="Accessibility audit targets.")
    hooks: List[str] = Field(default_factory=list, description="Hook side effect targets.")
    conditional_rendering: List[str] = Field(default_factory=list, description="Conditional branch test targets.")
    error_handling: List[str] = Field(default_factory=list, description="Error boundary / exception targets.")
    async_behavior: List[str] = Field(default_factory=list, description="Async / timer / promise targets.")
    integration: List[str] = Field(default_factory=list, description="Component composition targets.")
    performance: List[str] = Field(default_factory=list, description="Re-render & memoization targets.")
    regression: List[str] = Field(default_factory=list, description="Regression scenario targets.")
    mock_dependencies: List[str] = Field(default_factory=list, description="Services / modules requiring mocks.")
    recommended_rtl_queries: List[str] = Field(default_factory=list, description="Preferred RTL query methods.")
    preferred_assertions: List[str] = Field(default_factory=list, description="Preferred assertion matchers.")
    mock_requirements: List[str] = Field(default_factory=list, description="Mock initialization specs.")


class ComponentIR(BaseModel):
    """Normalized Component representation."""

    name: str = Field(..., description="Component name.")
    file_path: str = Field(..., description="Relative path to component file.")
    type: str = Field(..., description="Component paradigm: 'functional', 'class', 'angular_component'.")
    props_inputs: List[Dict[str, Any]] = Field(default_factory=list, description="Props or @Input bindings.")
    outputs_events: List[Dict[str, Any]] = Field(default_factory=list, description="Outputs or EventEmitter bindings.")

    # ---- Enriched fields (v2 & v3) ----
    id: Optional[str] = Field(None, description="Stable component ID.")
    project_id: Optional[str] = Field(None, description="Unique project identifier.")
    pipeline_run_id: Optional[str] = Field(None, description="Unique pipeline run identifier.")
    source_file: Optional[str] = Field(None, description="Relative path to component source file.")
    parent: Optional[str] = Field(None, description="Parent component name.")
    parent_id: Optional[str] = Field(None, description="Parent component ID.")
    children: List[str] = Field(default_factory=list, description="Child component names.")
    children_ids: List[str] = Field(default_factory=list, description="Child component IDs.")
    depth: int = Field(0, ge=0, description="Hierarchy depth.")
    risk_score: float = Field(0.0, ge=0.0, description="Inferred risk/testing priority score.")
    accessibility: Optional[AccessibilityInfo] = Field(None, description="Accessibility details.")
    testing_metadata: Optional[TestingMetadata] = Field(None, description="Testing recommendations.")
    dependency_graph: Optional[DependencyNode] = Field(None, description="Imports dependencies.")
    forms: List[FormModel] = Field(default_factory=list, description="Forms defined in this component.")

    # ---- Semantic Model Additions (v3) ----
    hooks: List[HookInfo] = Field(default_factory=list, description="Extracted hook details.")
    interaction_graph: List[InteractionGraphNode] = Field(default_factory=list, description="User action to DOM mutation graph.")
    state_transitions: List[StateTransition] = Field(default_factory=list, description="State transition graph.")
    render_conditions: List[RenderCondition] = Field(default_factory=list, description="Conditional rendering rules.")
    data_flow: Optional[DataFlowInfo] = Field(None, description="Data flow mapping.")
    accessibility_detail: Optional[AccessibilityDetail] = Field(None, description="Rich WCAG accessibility breakdown.")
    risk_analysis: Optional[RiskAnalysis] = Field(None, description="Dynamic weighted risk analysis.")
    testability: Optional[ComponentTestability] = Field(None, description="Intelligent testability metadata.")
    behavior_summary: Optional[str] = Field(None, description="Semantic summary of component behavior.")


class ExistingTestModel(BaseModel):
    """Normalized existing test file representation."""

    file_path: str = Field(..., description="Relative path to existing test/spec file.")
    type: str = Field(..., description="Test classification: 'test' or 'spec'.")


class FrameworkAgnosticIR(BaseModel):
    """Framework-Agnostic Intermediate Representation (IR).

    Serves as the common data contract for downstream modules (Module 5-8).
    """

    project_name: str = Field("IngestedProject", description="Name of the project.")
    project_id: Optional[str] = Field(None, description="Unique project identifier.")
    pipeline_run_id: Optional[str] = Field(None, description="Unique pipeline run identifier.")
    framework: str = Field(..., description="Detected original framework name.")
    components: List[ComponentIR] = Field(default_factory=list)
    elements: List[UIElement] = Field(default_factory=list)
    events: List[UIEvent] = Field(default_factory=list)
    state: List[ComponentState] = Field(default_factory=list)
    forms: List[FormModel] = Field(default_factory=list)
    services: List[ServiceDependency] = Field(default_factory=list)
    routes: List[RouteModel] = Field(default_factory=list)
    dependencies: List[Dict[str, Any]] = Field(default_factory=list)
    existing_tests: List[ExistingTestModel] = Field(default_factory=list)

    # ---- Enriched fields (v2) ----
    component_relationships: List[ComponentRelationshipInfo] = Field(
        default_factory=list,
        description="Hierarchy relationship information.",
    )
    dependency_graph: List[DependencyNode] = Field(
        default_factory=list,
        description="Dependency relationships.",
    )
    test_mapping: List[TestMapping] = Field(
        default_factory=list,
        description="Component-to-test-file mappings.",
    )
