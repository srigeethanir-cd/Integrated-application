"""
Pydantic models for Project Analyzer & Parser (Module 3).

Enhanced with rich semantic information for high-quality frontend unit test
generation.  All new fields use ``Optional`` with ``None`` defaults or
``default_factory=list`` so that downstream consumers (Modules 4–9) remain
fully backward-compatible without any modification.

Hierarchy
---------
Shared (new):  AccessibilityInfo, TestingMetadata, ComponentRelationshipInfo,
               DependencyNode, TestMapping, FormFieldAnalysis, FormAnalysis,
               RoutingInfo, ContextUsage
Shared:        ImportInfo, ExportInfo, FunctionInfo, ApiCallInfo,
               ExistingTestInfo
React:         PropInfo, StateInfo, HookInfo, EventHandlerInfo, JsxElementInfo
               → ReactComponentInfo → ReactAnalysisResult
Angular:       DecoratorInfo, InputInfo, OutputInfo, InjectedServiceInfo,
               ReactiveFormInfo, TemplateBindingInfo, RouteInfo
               → AngularComponentInfo, AngularServiceInfo, AngularModuleInfo
               → AngularAnalysisResult
Top-level:     AnalyzerRequest, AnalyzerResponse
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field, field_validator


# =========================================================================
# New shared semantic models (added in v2 enrichment)
# =========================================================================


class AccessibilityInfo(BaseModel):
    """ARIA and semantic-HTML accessibility metadata extracted from a component."""

    aria_attributes: Dict[str, Optional[str]] = Field(
        default_factory=dict,
        description="Map of aria-* attribute names to their values.",
    )
    roles: List[str] = Field(
        default_factory=list,
        description="role attribute values found in this component.",
    )
    keyboard_events: List[str] = Field(
        default_factory=list,
        description="Keyboard event handlers found (e.g. 'onKeyDown', 'onKeyUp').",
    )
    has_focus_management: bool = Field(
        False,
        description="True if the component contains focus() calls or autoFocus.",
    )
    alt_texts: List[str] = Field(
        default_factory=list,
        description="alt attribute values from <img> or icon elements.",
    )
    label_associations: List[str] = Field(
        default_factory=list,
        description="htmlFor / aria-labelledby values linking labels to inputs.",
    )
    accessible_elements: List[str] = Field(
        default_factory=list,
        description="JSX tags that carry accessible attributes (role, aria-*, alt).",
    )


class TestingMetadata(BaseModel):
    """Framework-agnostic testing metadata generated for every component."""

    testable_elements: List[str] = Field(
        default_factory=list,
        description="Element tags / component names that can be asserted on.",
    )
    interactive_elements: List[str] = Field(
        default_factory=list,
        description="Elements with on* event handlers (buttons, inputs, links).",
    )
    mock_dependencies: List[str] = Field(
        default_factory=list,
        description="Service / API function names that must be mocked in tests.",
    )
    recommended_test_categories: List[str] = Field(
        default_factory=list,
        description=(
            "Suggested test categories based on what was found: "
            "'Rendering', 'Events', 'State', 'Forms', 'API', 'Accessibility', "
            "'Routing', 'Context'."
        ),
    )
    recommended_queries: List[Dict[str, str]] = Field(
        default_factory=list,
        description="Recommended testing library / Angular queries (e.g. {query: 'getByRole', target: 'button'}).",
    )
    edge_cases: List[str] = Field(
        default_factory=list,
        description="Potential edge case scenarios identified for testing.",
    )
    negative_scenarios: List[str] = Field(
        default_factory=list,
        description="Negative test scenarios (e.g. invalid submission, network error).",
    )
    suggested_mocks: List[Dict[str, str]] = Field(
        default_factory=list,
        description="Suggested mocks needed for component dependencies.",
    )


class ComponentRelationshipInfo(BaseModel):
    """Parent-child wiring for a single component in the component tree."""

    component: str = Field(..., description="Component name.")
    parent: Optional[str] = Field(None, description="Name of the parent component, if known.")
    children: List[str] = Field(
        default_factory=list,
        description="Names of child components rendered by this component.",
    )
    depth: int = Field(0, ge=0, description="Depth in the component tree (root = 0).")


class DependencyNode(BaseModel):
    """Dependency graph node for a single component."""

    component: str = Field(..., description="Component name.")
    imports_components: List[str] = Field(
        default_factory=list,
        description="Other React/Angular components imported by this component.",
    )
    imports_services: List[str] = Field(
        default_factory=list,
        description="Service / API modules imported by this component.",
    )
    imports_utilities: List[str] = Field(
        default_factory=list,
        description="Utility / helper modules imported by this component.",
    )
    imports_contexts: List[str] = Field(
        default_factory=list,
        description="React Context objects imported by this component.",
    )
    imports_hooks: List[str] = Field(
        default_factory=list,
        description="Custom React hooks imported by this component.",
    )
    imports_stores: List[str] = Field(
        default_factory=list,
        description="State management stores (Redux, Zustand, RxJS) imported.",
    )
    imports_external_libraries: List[str] = Field(
        default_factory=list,
        description="External third-party libraries imported.",
    )


class TestMapping(BaseModel):
    """Maps a component to its associated test file and coverage details."""

    component: str = Field(..., description="Component name.")
    test_file: Optional[str] = Field(None, description="Relative path to the test file.")
    testing_framework: Optional[str] = Field(
        None,
        description="Inferred testing framework: 'jest', 'jasmine', 'vitest', etc.",
    )
    covered_features: List[str] = Field(
        default_factory=list,
        description="Features/scenarios covered based on test describe/it labels.",
    )


class FormFieldAnalysis(BaseModel):
    """A single form field (input, select, textarea) within a form."""

    name: str = Field(..., description="Field name (from name or id attribute).")
    field_type: str = Field("text", description="Input type (text, email, password, checkbox, etc.).")
    is_controlled: bool = Field(
        False,
        description="True if the field has both value= and onChange= (controlled input).",
    )
    is_required: bool = Field(False, description="True if the required attribute is present.")
    validation_rules: List[str] = Field(
        default_factory=list,
        description="Detected validation rules (required, minLength, pattern, etc.).",
    )
    error_message: Optional[str] = Field(
        None,
        description="Validation error message text associated with this field.",
    )
    label: Optional[str] = Field(
        None,
        description="Associated field label text.",
    )
    placeholder: Optional[str] = Field(
        None,
        description="Placeholder text.",
    )


class FormAnalysis(BaseModel):
    """A form element and its analysis for test generation."""

    element: str = Field("form", description="Root element tag (usually 'form').")
    is_controlled: bool = Field(
        False,
        description="True if ALL inputs in the form are controlled.",
    )
    submit_handler: Optional[str] = Field(
        None, description="onSubmit handler function name."
    )
    reset_handler: Optional[str] = Field(
        None, description="onReset handler function name."
    )
    library: Optional[str] = Field(
        None,
        description="Form library detected: 'formik', 'react-hook-form', 'native', etc.",
    )
    fields: List[FormFieldAnalysis] = Field(
        default_factory=list, description="Detected form fields."
    )


class RoutingInfo(BaseModel):
    """React Router / Angular Router usage detected in a component."""

    links: List[str] = Field(
        default_factory=list,
        description="Link / NavLink to= paths.",
    )
    routes: List[str] = Field(
        default_factory=list,
        description="Route path= values defined in this component.",
    )
    uses_navigate: bool = Field(
        False,
        description="True if useNavigate() or useHistory() is used.",
    )
    uses_router_push: bool = Field(
        False,
        description="True if router.push / history.push is called.",
    )
    route_params: List[str] = Field(
        default_factory=list,
        description="Route parameter names read via useParams / ActivatedRoute.",
    )
    redirects: List[str] = Field(
        default_factory=list,
        description="<Redirect to= /> or navigate() target paths.",
    )


class ContextUsage(BaseModel):
    """React Context API usage within a component."""

    context_name: str = Field(..., description="Context variable or display name.")
    is_provider: bool = Field(False, description="True if this component is a Provider.")
    is_consumer: bool = Field(False, description="True if useContext / Consumer is used.")
    values_provided: List[str] = Field(
        default_factory=list,
        description="Keys provided via the value= prop of the Provider.",
    )


# =========================================================================
# Shared models (used by both React and Angular)
# =========================================================================


class ImportInfo(BaseModel):
    """A single import statement."""

    source: str = Field(..., description="Module specifier (e.g. 'react', './AuthService').")
    specifiers: List[str] = Field(default_factory=list, description="Imported names.")
    is_default: bool = Field(False, description="True if this is a default import.")


class ExportInfo(BaseModel):
    """A single export declaration."""

    name: str = Field(..., description="Exported identifier name.")
    is_default: bool = Field(False, description="True if this is the default export.")


class FunctionInfo(BaseModel):
    """A function or method signature."""

    name: str = Field(..., description="Function name.")
    params: List[str] = Field(default_factory=list, description="Parameter names.")
    is_async: bool = Field(False, description="True if the function is async.")


class ApiCallInfo(BaseModel):
    """An API or service call detected in the source.

    All fields below the original two are new additions; they default to
    ``None`` / ``False`` so existing consumers see no change.
    """

    # ---- Original fields (preserved) ----
    function_name: str = Field(..., description="Callee expression (e.g. 'fetch', 'axios.get').")
    type: str = Field(..., description="Call type: 'fetch', 'axios', 'service_call'.")

    # ---- New enrichment fields ----
    endpoint: Optional[str] = Field(
        None, description="URL or endpoint path (first string argument if detectable)."
    )
    http_method: Optional[str] = Field(
        None,
        description="HTTP method: 'GET', 'POST', 'PUT', 'DELETE', 'PATCH'.",
    )
    is_async: bool = Field(False, description="True if the call is inside an async function.")
    has_error_handling: bool = Field(
        False,
        description="True if the call is wrapped in try/catch or .catch().",
    )
    in_use_effect: bool = Field(
        False,
        description="True if the call is inside a useEffect callback.",
    )
    loading_state_var: Optional[str] = Field(
        None,
        description="Loading state variable name associated with this call (heuristic).",
    )
    trigger: Optional[str] = Field(
        None,
        description="Triggering event or lifecycle context (e.g. 'onSubmit', 'useEffect').",
    )


class ExistingTestInfo(BaseModel):
    """An existing test file found in the project."""

    file_path: str = Field(..., description="Relative path to the test file.")
    type: str = Field(..., description="Test file type: 'test' or 'spec'.")


# =========================================================================
# React-specific models
# =========================================================================


class PropInfo(BaseModel):
    """A React component prop."""

    name: str = Field(..., description="Prop name.")
    type: str = Field("any", description="Declared type (e.g. 'string', 'function').")
    required: bool = Field(False, description="True if the prop is required.")
    default_value: Optional[str] = Field(None, description="Default value as source text.")
    usage: List[str] = Field(
        default_factory=list,
        description="JSX element tags or handlers that read or invoke this prop.",
    )


class StateInfo(BaseModel):
    """A React useState hook call.

    New fields ``state_type``, ``used_in``, and ``updated_by`` are additive;
    they default to safe empty values so Modules 4–9 are unaffected.
    """

    # ---- Original fields (preserved) ----
    name: str = Field(..., description="State variable name.")
    setter: str = Field(..., description="Setter function name.")
    initial_value: Optional[str] = Field(None, description="Initial value as source text.")

    # ---- New enrichment fields ----
    state_type: str = Field(
        "unknown",
        description=(
            "Inferred type from initial value: 'boolean', 'string', 'number', "
            "'array', 'object', 'null', 'unknown'."
        ),
    )
    used_in: List[str] = Field(
        default_factory=list,
        description="JSX element tags or component names that read this state variable.",
    )
    updated_by: List[str] = Field(
        default_factory=list,
        description="Handler / function names that call the setter.",
    )
    management_type: str = Field(
        "useState",
        description="State classification: 'useState', 'useReducer', 'redux', 'zustand', 'context'.",
    )


class HookInfo(BaseModel):
    """A React hook invocation.

    New fields ``is_custom``, ``params``, and ``return_values`` are additive.
    """

    # ---- Original fields (preserved) ----
    name: str = Field(..., description="Hook name (e.g. 'useState', 'useEffect').")
    count: int = Field(1, ge=1, description="Number of times this hook is called.")
    dependencies: List[str] = Field(
        default_factory=list,
        description="Dependency array entries (for useEffect/useMemo/useCallback).",
    )

    # ---- New enrichment fields ----
    is_custom: bool = Field(
        False,
        description="True if this is a project-defined custom hook (not React built-in).",
    )
    params: List[str] = Field(
        default_factory=list,
        description="Arguments passed to the hook call (as source text).",
    )
    return_values: List[str] = Field(
        default_factory=list,
        description="Destructured return values from the hook (e.g. ['data', 'loading']).",
    )
    side_effects: List[str] = Field(
        default_factory=list,
        description="Side-effects executed inside the hook callback (API calls, state updates).",
    )


class EventHandlerInfo(BaseModel):
    """An event handler detected in JSX.

    New fields describe what the handler does: which state it mutates, which
    services it calls, whether it navigates, and DOM behaviour modifiers.
    """

    # ---- Original fields (preserved) ----
    name: str = Field(..., description="Handler function name.")
    event_type: str = Field(..., description="Event attribute (e.g. 'onClick', 'onChange').")

    # ---- New enrichment fields ----
    element: Optional[str] = Field(
        None,
        description="JSX element tag to which this handler is attached (e.g. 'button', 'form').",
    )
    updates_state: List[str] = Field(
        default_factory=list,
        description="State variable names that this handler updates via their setter.",
    )
    service_calls: List[str] = Field(
        default_factory=list,
        description="API / service function names called inside this handler.",
    )
    navigation: bool = Field(
        False,
        description="True if the handler triggers client-side navigation.",
    )
    prevent_default: bool = Field(
        False,
        description="True if the handler calls e.preventDefault().",
    )
    stop_propagation: bool = Field(
        False,
        description="True if the handler calls e.stopPropagation().",
    )


class JsxElementInfo(BaseModel):
    """A JSX element detected in the component render.

    New attribute fields provide the data needed to generate element locators,
    ARIA assertions, and value-binding tests without natural-language inference.
    """

    # ---- Original fields (preserved) ----
    tag: str = Field(..., description="Element tag name (e.g. 'form', 'input', 'Button').")
    attributes: List[str] = Field(
        default_factory=list, description="Attribute/prop names on this element."
    )
    children_count: int = Field(0, ge=0, description="Number of direct children.")

    # ---- New enrichment fields ----
    id: Optional[str] = Field(None, description="id attribute value.")
    class_name: Optional[str] = Field(None, description="className attribute value.")
    role: Optional[str] = Field(None, description="role attribute value.")
    aria_label: Optional[str] = Field(None, description="aria-label attribute value.")
    aria_expanded: Optional[str] = Field(None, description="aria-expanded attribute value.")
    placeholder: Optional[str] = Field(None, description="placeholder attribute value.")
    alt: Optional[str] = Field(None, description="alt attribute value.")
    disabled: Optional[str] = Field(
        None, description="disabled attribute value, or 'true' if present as a boolean."
    )
    required: Optional[str] = Field(
        None, description="required attribute value, or 'true' if present as a boolean."
    )
    value_binding: Optional[str] = Field(
        None, description="value= attribute binding (source text)."
    )
    event_bindings: List[Dict[str, str]] = Field(
        default_factory=list,
        description="List of {event, handler} pairs (e.g. {event: 'onClick', handler: 'handleClick'}).",
    )


class ReactComponentInfo(BaseModel):
    """Full extraction result for a single React component.

    Original fields are preserved.  Enriched semantic fields appended.
    """

    # ---- Original fields (preserved) ----
    file_path: str = Field(..., description="Relative path to the source file.")
    name: str = Field(..., description="Component name.")
    type: str = Field(..., description="Component type: 'functional' or 'class'.")
    props: List[PropInfo] = Field(default_factory=list)
    state: List[StateInfo] = Field(default_factory=list)
    hooks: List[HookInfo] = Field(default_factory=list)
    jsx_elements: List[JsxElementInfo] = Field(default_factory=list)
    event_handlers: List[EventHandlerInfo] = Field(default_factory=list)
    functions: List[FunctionInfo] = Field(default_factory=list)
    imports: List[ImportInfo] = Field(default_factory=list)
    exports: List[ExportInfo] = Field(default_factory=list)
    api_calls: List[ApiCallInfo] = Field(default_factory=list)

    # ---- Enrichment fields ----
    parent_component: Optional[str] = Field(
        None,
        description="Name of the parent component that renders this one (computed post-parse).",
    )
    child_components: List[str] = Field(
        default_factory=list,
        description="Names of child (custom) components rendered by this component.",
    )
    forms: List[FormAnalysis] = Field(
        default_factory=list,
        description="Form elements and their analysis.",
    )
    routing_info: Optional[RoutingInfo] = Field(
        None,
        description="React Router usage detected in this component.",
    )
    context_usage: List[ContextUsage] = Field(
        default_factory=list,
        description="React Context API usage (Provider, Consumer, useContext).",
    )
    accessibility: Optional[AccessibilityInfo] = Field(
        None,
        description="Aggregated accessibility metadata for this component.",
    )
    testing_metadata: Optional[TestingMetadata] = Field(
        None,
        description="Framework-agnostic testing metadata generated from analysis.",
    )
    dependency_graph: Optional[DependencyNode] = Field(
        None,
        description="Dependency graph node showing what this component imports.",
    )
    conditional_rendering: List[Dict[str, Any]] = Field(
        default_factory=list,
        description=(
            "Conditional rendering patterns found in JSX: each entry has "
            "{'type': 'ternary'|'logical_and'|'logical_or', 'condition': str, "
            "'consequent': str, 'alternate': str}."
        ),
    )
    event_flows: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Event → handler → state update → API call → navigation flow chains.",
    )
    business_purpose: Optional[str] = Field(
        None,
        description="Inferred business domain/purpose of the component.",
    )
    complexity_score: int = Field(
        1, ge=1,
        description="Estimated structural complexity score (1-10).",
    )
    risk_score: int = Field(
        1, ge=1, le=10,
        description="Estimated risk score based on state complexity, forms, and API usage (1-10).",
    )
    test_priority: str = Field(
        "medium",
        description="Recommended test priority: 'high', 'medium', or 'low'.",
    )
    confidence_score: float = Field(
        1.0, ge=0.0, le=1.0,
        description="Analysis confidence level (0.0 to 1.0).",
    )


class ReactAnalysisResult(BaseModel):
    """Aggregated analysis result for a React project.

    Enriched top-level arrays provide cross-component insight and coverage gap metrics.
    """

    # ---- Original fields (preserved) ----
    components: List[ReactComponentInfo] = Field(default_factory=list)
    existing_tests: List[ExistingTestInfo] = Field(default_factory=list)
    files_analyzed: int = Field(0, ge=0)

    # ---- Enrichment fields ----
    component_relationships: List[ComponentRelationshipInfo] = Field(
        default_factory=list,
        description="Parent-child wiring for all components in the project.",
    )
    dependency_graph: List[DependencyNode] = Field(
        default_factory=list,
        description="Dependency graph nodes for every component in the project.",
    )
    test_mapping: List[TestMapping] = Field(
        default_factory=list,
        description="Component-to-test-file mappings.",
    )
    uncovered_components: List[str] = Field(
        default_factory=list,
        description="Component names that lack corresponding unit test files.",
    )
    coverage_gaps: List[str] = Field(
        default_factory=list,
        description="Identified coverage gap descriptions across components.",
    )
    duplicate_tests: List[str] = Field(
        default_factory=list,
        description="Multiple test files targeting identical components.",
    )


# =========================================================================
# Angular-specific models
# =========================================================================


class DecoratorInfo(BaseModel):
    """An Angular/TypeScript decorator."""

    name: str = Field(..., description="Decorator name (e.g. 'Component', 'Injectable').")
    arguments: Dict[str, Any] = Field(
        default_factory=dict, description="Decorator argument object."
    )


class InputInfo(BaseModel):
    """An Angular @Input() property."""

    name: str = Field(..., description="Property name.")
    type: str = Field("any", description="Declared TypeScript type.")
    alias: Optional[str] = Field(None, description="Binding alias if specified.")
    required: bool = Field(False, description="True if the input is required.")


class OutputInfo(BaseModel):
    """An Angular @Output() property."""

    name: str = Field(..., description="Property name.")
    type: str = Field("EventEmitter", description="EventEmitter generic type.")


class InjectedServiceInfo(BaseModel):
    """A service injected via constructor DI."""

    name: str = Field(..., description="Constructor parameter name.")
    type: str = Field(..., description="TypeScript type of the injected service.")


class ReactiveFormInfo(BaseModel):
    """A reactive form detected in the component."""

    name: str = Field(..., description="FormGroup variable name.")
    controls: List[str] = Field(default_factory=list, description="Form control names.")
    validators: List[str] = Field(default_factory=list, description="Applied validators.")


class TemplateBindingInfo(BaseModel):
    """Template bindings extracted from an Angular HTML template."""

    property_bindings: List[str] = Field(default_factory=list, description="[prop] bindings.")
    event_bindings: List[str] = Field(default_factory=list, description="(event) bindings.")
    interpolations: List[str] = Field(default_factory=list, description="{{ expr }} interpolations.")
    structural_directives: List[str] = Field(
        default_factory=list, description="*ngIf, *ngFor, etc."
    )


class RouteInfo(BaseModel):
    """A route definition from the Angular routing module."""

    path: str = Field(..., description="Route path.")
    component: Optional[str] = Field(None, description="Target component name.")
    guard: Optional[str] = Field(None, description="Route guard name.")
    lazy_loaded: bool = Field(False, description="True if the route is lazy-loaded.")


class AngularComponentInfo(BaseModel):
    """Full extraction result for a single Angular component.

    Original fields are preserved. Enriched semantic fields appended.
    """

    # ---- Original fields (preserved) ----
    file_path: str = Field(..., description="Relative path to the source file.")
    name: str = Field(..., description="Component class name.")
    selector: Optional[str] = Field(None, description="CSS selector from @Component.")
    template_file: Optional[str] = Field(None, description="External template filename.")
    style_files: List[str] = Field(default_factory=list, description="External style filenames.")
    decorators: List[DecoratorInfo] = Field(default_factory=list)
    inputs: List[InputInfo] = Field(default_factory=list)
    outputs: List[OutputInfo] = Field(default_factory=list)
    injected_services: List[InjectedServiceInfo] = Field(default_factory=list)
    reactive_forms: List[ReactiveFormInfo] = Field(default_factory=list)
    template_bindings: Optional[TemplateBindingInfo] = Field(None)
    methods: List[FunctionInfo] = Field(default_factory=list)
    lifecycle_hooks: List[str] = Field(default_factory=list)
    imports: List[ImportInfo] = Field(default_factory=list)
    exports: List[ExportInfo] = Field(default_factory=list)

    # ---- Enrichment fields ----
    child_components: List[str] = Field(
        default_factory=list,
        description="Child component selectors found in the template.",
    )
    accessibility: Optional[AccessibilityInfo] = Field(
        None,
        description="Accessibility metadata extracted from the template.",
    )
    testing_metadata: Optional[TestingMetadata] = Field(
        None,
        description="Framework-agnostic testing metadata for this component.",
    )
    api_calls: List[ApiCallInfo] = Field(
        default_factory=list,
        description="HTTP / service calls found in component methods.",
    )
    conditional_rendering: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Template structural directives (*ngIf, *ngFor, *ngSwitch) or conditions.",
    )
    event_flows: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Event → method → service call → state update flows.",
    )
    business_purpose: Optional[str] = Field(
        None,
        description="Inferred business domain purpose of the component.",
    )
    complexity_score: int = Field(
        1, ge=1,
        description="Estimated structural complexity score (1-10).",
    )
    risk_score: int = Field(
        1, ge=1, le=10,
        description="Estimated risk score based on state complexity, forms, and API usage (1-10).",
    )
    test_priority: str = Field(
        "medium",
        description="Recommended test priority: 'high', 'medium', or 'low'.",
    )
    confidence_score: float = Field(
        1.0, ge=0.0, le=1.0,
        description="Analysis confidence level (0.0 to 1.0).",
    )


class AngularServiceInfo(BaseModel):
    """Full extraction result for a single Angular service."""

    # ---- Original fields (preserved) ----
    file_path: str = Field(..., description="Relative path to the source file.")
    name: str = Field(..., description="Service class name.")
    decorators: List[DecoratorInfo] = Field(default_factory=list)
    provided_in: Optional[str] = Field(None, description="providedIn value (e.g. 'root').")
    methods: List[FunctionInfo] = Field(default_factory=list)
    injected_services: List[InjectedServiceInfo] = Field(default_factory=list)

    # ---- Enrichment fields ----
    api_calls: List[ApiCallInfo] = Field(
        default_factory=list,
        description="HTTP client calls found in this service's methods.",
    )


class AngularModuleInfo(BaseModel):
    """Full extraction result for a single Angular @NgModule."""

    file_path: str = Field(..., description="Relative path to the source file.")
    name: str = Field(..., description="Module class name.")
    declarations: List[str] = Field(default_factory=list)
    imports: List[str] = Field(default_factory=list)
    providers: List[str] = Field(default_factory=list)
    exports: List[str] = Field(default_factory=list)


class AngularAnalysisResult(BaseModel):
    """Aggregated analysis result for an Angular project."""

    # ---- Original fields (preserved) ----
    components: List[AngularComponentInfo] = Field(default_factory=list)
    services: List[AngularServiceInfo] = Field(default_factory=list)
    modules: List[AngularModuleInfo] = Field(default_factory=list)
    routing: List[RouteInfo] = Field(default_factory=list)
    existing_tests: List[ExistingTestInfo] = Field(default_factory=list)
    files_analyzed: int = Field(0, ge=0)

    # ---- Enrichment fields ----
    component_relationships: List[ComponentRelationshipInfo] = Field(
        default_factory=list,
        description="Parent-child wiring for all Angular components.",
    )
    dependency_graph: List[DependencyNode] = Field(
        default_factory=list,
        description="Dependency graph nodes for every component and service.",
    )
    test_mapping: List[TestMapping] = Field(
        default_factory=list,
        description="Component/service-to-spec-file mappings.",
    )
    uncovered_components: List[str] = Field(
        default_factory=list,
        description="Component names that lack corresponding unit test files.",
    )
    coverage_gaps: List[str] = Field(
        default_factory=list,
        description="Identified coverage gap descriptions across components.",
    )
    duplicate_tests: List[str] = Field(
        default_factory=list,
        description="Multiple test files targeting identical components.",
    )


# =========================================================================
# Top-level request / response
# =========================================================================


class AnalyzerRequest(BaseModel):
    """Request body for the project analyzer endpoint."""

    project_path: str = Field(
        ...,
        min_length=1,
        description="Absolute path to the project source directory.",
        examples=["/home/user/uploads/abc123/source"],
    )

    @field_validator("project_path")
    @classmethod
    def validate_project_path(cls, value: str) -> str:
        if not Path(value).is_absolute():
            raise ValueError("project_path must be an absolute path.")
        return value


class AnalyzerResponse(BaseModel):
    """Top-level response from the project analyzer.

    The ``analysis`` field carries a framework-specific result:
    ``ReactAnalysisResult`` when ``framework`` is React / Next.js,
    ``AngularAnalysisResult`` when ``framework`` is Angular.
    """

    framework: str = Field(..., description="Detected framework name.")
    project_path: str = Field(..., description="Analysed project path.")
    files_analyzed: int = Field(0, ge=0, description="Total source files parsed.")
    analysis: Union[ReactAnalysisResult, AngularAnalysisResult] = Field(
        ..., description="Framework-specific analysis payload."
    )
