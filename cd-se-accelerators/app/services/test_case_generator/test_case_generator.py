"""
TestCase Generator Implementations & Service – Module 7.

Implements concrete generators for all categories, the main orchestrator
TestCaseGeneratorService, deduplication, and thorough schema validation.
"""

import logging
from typing import Any, Dict, List, Optional, Set, Union
from app.models.strategy_models import StrategyPlanResponse, TestStrategy
from app.models.edge_case_models import EdgeCasePlanResponse, EdgeCaseScenario
from app.models.test_case_models import TestCase, TestCasePlanRequest, TestCasePlanResponse, TestCaseLocator, TestCaseMetadata, TestCaseStep, TestCaseTraceability
from app.services.test_case_generator.base_generator import BaseTestCaseGenerator
from app.services.test_case_generator.test_case_registry import TestCaseRegistry
from app.models.ir_models import FrameworkAgnosticIR
from app.utils.ir_cache import get_cached_ir

logger = logging.getLogger(__name__)


def _extract_traceability(strategy: TestStrategy, edge_case: EdgeCaseScenario) -> Dict[str, Any]:
    """Helper to extract traceability fields from strategy and edge case."""
    comp_id = strategy.component_id or edge_case.component_id or f"comp_{strategy.target_component}"
    proj_id = strategy.project_id or getattr(edge_case, "project_id", None)
    pipe_run_id = strategy.pipeline_run_id or getattr(edge_case, "pipeline_run_id", None)
    src_file = strategy.source_file or getattr(edge_case, "source_file", None)

    trace_obj = TestCaseTraceability(
        strategy_id=strategy.id,
        edge_case_id=edge_case.id,
        component_id=comp_id,
        project_id=proj_id,
        pipeline_run_id=pipe_run_id,
        source_file=src_file,
        element_id=strategy.element_id or edge_case.element_id,
        event_id=strategy.event_id or edge_case.event_id,
        state_id=strategy.state_id or edge_case.state_id,
        service_id=strategy.service_id or edge_case.service_id,
        route_id=strategy.route_id or edge_case.route_id,
    )

    return {
        "component_id": comp_id,
        "element_id": strategy.element_id or edge_case.element_id,
        "event_id": strategy.event_id or edge_case.event_id,
        "state_id": strategy.state_id or edge_case.state_id,
        "service_id": strategy.service_id or edge_case.service_id,
        "route_id": strategy.route_id or edge_case.route_id,
        "traceability": trace_obj,
    }


class ComponentTestCaseGenerator(BaseTestCaseGenerator):
    """Generates test cases for component mounting, rendering, and conditional layout rendering."""

    @property
    def category_name(self) -> str:
        return "State"

    def supports(self, strategy: TestStrategy, edge_case: EdgeCaseScenario) -> bool:
        return (
            edge_case.category == "State"
            and strategy.category in ("Component Initialization", "Rendering Tests", "Conditional Rendering Tests")
        )

    def generate(self, strategy: TestStrategy, edge_case: EdgeCaseScenario) -> TestCase:
        test_data = dict(edge_case.input_data) if edge_case.input_data else {"render_context": "default_initialization"}
        comp = strategy.target_component

        return TestCase(
            id=f"TC-{strategy.id}-{edge_case.id.replace('EC-' + strategy.id + '-', '')}",
            strategy_id=strategy.id,
            edge_case_id=edge_case.id,
            category=edge_case.category,
            priority=strategy.priority,
            component=comp,
            title=f"Component: {comp} - {edge_case.title}",
            objective=f"Verify component {comp} rendering/initialization state under edge condition: '{edge_case.title}'.",
            preconditions=list(strategy.preconditions) + ["DOM simulator is available"],
            steps=[
                f"Set up test environment and mock inputs with: {test_data}",
                f"Mount/Render target component '{comp}' in testing container",
                "Query visual elements in layout to inspect DOM nodes and attributes",
                f"Assert visual output matches condition: '{edge_case.expected_behavior}'"
            ],
            test_data=test_data,
            expected_result=edge_case.expected_behavior,
            tags=list(strategy.coverage_tags) + list(edge_case.tags) + ["component", "rendering"],
            metadata=TestCaseMetadata(
                component=comp,
                element="container",
                element_type="container",
                locator=TestCaseLocator(strategy="tag", value="div"),
                action="render",
                assertion_type="exists",
                assertion_target="component",
                expected_value="visible",
                mock_required=False,
                mock_services=[],
                pre_test_state={},
                post_test_state={"mounted": True},
                dependencies=[],
                accessibility_checks=[],
                cleanup_actions=["unmount"]
            ),
            **_extract_traceability(strategy, edge_case)
        )


class FormTestCaseGenerator(BaseTestCaseGenerator):
    """Generates test cases for reactive forms and input validation fields."""

    @property
    def category_name(self) -> str:
        return "Forms"

    def supports(self, strategy: TestStrategy, edge_case: EdgeCaseScenario) -> bool:
        return edge_case.category == "Forms" and strategy.category == "Form Validation Tests"

    def generate(self, strategy: TestStrategy, edge_case: EdgeCaseScenario) -> TestCase:
        test_data = dict(edge_case.input_data) if edge_case.input_data else {"form_payload": {"email": "", "password": ""}}
        comp = strategy.target_component

        return TestCase(
            id=f"TC-{strategy.id}-{edge_case.id.replace('EC-' + strategy.id + '-', '')}",
            strategy_id=strategy.id,
            edge_case_id=edge_case.id,
            category=edge_case.category,
            priority=strategy.priority,
            component=comp,
            title=f"Form: {comp} - {edge_case.title}",
            objective=f"Validate reactive form control bounds and inputs in component '{comp}' for: '{edge_case.title}'.",
            preconditions=list(strategy.preconditions) + ["Reactive forms module is configured"],
            steps=[
                f"Render target form component '{comp}'",
                "Locate input controls and form validation error containers",
                f"Inject test data payload: {test_data} into form fields",
                "Trigger form validation check or submit action",
                f"Verify validation errors display or payload is rejected as expected: '{edge_case.expected_behavior}'"
            ],
            test_data=test_data,
            expected_result=edge_case.expected_behavior,
            tags=list(strategy.coverage_tags) + list(edge_case.tags) + ["form", "validation"],
            metadata=TestCaseMetadata(
                component=comp,
                element="form",
                element_type="form",
                locator=TestCaseLocator(strategy="role", value="form"),
                action="submit",
                assertion_type="validation",
                assertion_target="form_status",
                expected_value="invalid" if "error" in edge_case.id.lower() or "invalid" in edge_case.id.lower() else "valid",
                mock_required=False,
                mock_services=[],
                pre_test_state={"form_dirty": False},
                post_test_state={"form_submitted": True},
                dependencies=[],
                accessibility_checks=[],
                cleanup_actions=["reset_form"]
            ),
            **_extract_traceability(strategy, edge_case)
        )


class EventTestCaseGenerator(BaseTestCaseGenerator):
    """Generates test cases for pointer interactions and event handling logic."""

    @property
    def category_name(self) -> str:
        return "Events"

    def supports(self, strategy: TestStrategy, edge_case: EdgeCaseScenario) -> bool:
        return (
            edge_case.category == "Events"
            and strategy.category in ("Event Handling Tests", "User Interaction Tests")
        )

    def generate(self, strategy: TestStrategy, edge_case: EdgeCaseScenario) -> TestCase:
        test_data = dict(edge_case.input_data) if edge_case.input_data else {"event_trigger": "pointer_click"}
        comp = strategy.target_component

        is_click = "click" in strategy.id.lower() or "click" in strategy.description.lower()
        act = "click" if is_click else "type"
        el_type = "button" if is_click else "textbox"

        return TestCase(
            id=f"TC-{strategy.id}-{edge_case.id.replace('EC-' + strategy.id + '-', '')}",
            strategy_id=strategy.id,
            edge_case_id=edge_case.id,
            category=edge_case.category,
            priority=strategy.priority,
            component=comp,
            title=f"Event: {comp} - {edge_case.title}",
            objective=f"Assert component '{comp}' handles pointer/keyboard events correctly for: '{edge_case.title}'.",
            preconditions=list(strategy.preconditions) + ["Event simulators are loaded"],
            steps=[
                f"Mount component '{comp}' in active layout tree",
                "Query and target the specific interactive node bound to event handlers",
                f"Dispatch event mock with data: {test_data}",
                f"Verify event callback triggers actions cleanly as expected: '{edge_case.expected_behavior}'"
            ],
            test_data=test_data,
            expected_result=edge_case.expected_behavior,
            tags=list(strategy.coverage_tags) + list(edge_case.tags) + ["event", "interaction"],
            metadata=TestCaseMetadata(
                component=comp,
                element="interactive_element",
                element_type=el_type,
                locator=TestCaseLocator(strategy="role", value=el_type),
                action=act,
                assertion_type="callback_triggered",
                assertion_target="event_handler",
                expected_value=edge_case.expected_behavior,
                mock_required=False,
                mock_services=[],
                pre_test_state={},
                post_test_state={},
                dependencies=[],
                accessibility_checks=[],
                cleanup_actions=[]
            ),
            **_extract_traceability(strategy, edge_case)
        )


class StateTestCaseGenerator(BaseTestCaseGenerator):
    """Generates test cases for internal reactive state variables and hooks."""

    @property
    def category_name(self) -> str:
        return "State"

    def supports(self, strategy: TestStrategy, edge_case: EdgeCaseScenario) -> bool:
        return edge_case.category == "State" and strategy.category == "State Management Tests"

    def generate(self, strategy: TestStrategy, edge_case: EdgeCaseScenario) -> TestCase:
        test_data = dict(edge_case.input_data) if edge_case.input_data else {"state_action": "trigger_mutation"}
        comp = strategy.target_component
        state_var = strategy.id.split("-")[-1]

        return TestCase(
            id=f"TC-{strategy.id}-{edge_case.id.replace('EC-' + strategy.id + '-', '')}",
            strategy_id=strategy.id,
            edge_case_id=edge_case.id,
            category=edge_case.category,
            priority=strategy.priority,
            component=comp,
            title=f"State: {comp} - {edge_case.title}",
            objective=f"Verify state variable transitions and updates in '{comp}' for edge case: '{edge_case.title}'.",
            preconditions=list(strategy.preconditions) + ["State store or hook hook is initialized"],
            steps=[
                f"Render component '{comp}' with default initial state",
                f"Trigger action or state update sequence with parameters: {test_data}",
                "Monitor internal state transitions and trigger re-render cycle",
                f"Assert component visual attributes update: '{edge_case.expected_behavior}'"
            ],
            test_data=test_data,
            expected_result=edge_case.expected_behavior,
            tags=list(strategy.coverage_tags) + list(edge_case.tags) + ["state", "lifecycle"],
            metadata=TestCaseMetadata(
                component=comp,
                element=state_var,
                element_type="reactive_state",
                locator=TestCaseLocator(strategy="state_variable", value=state_var),
                action="state_update",
                assertion_type="state_value",
                assertion_target=state_var,
                expected_value=edge_case.expected_behavior,
                mock_required=False,
                mock_services=[],
                pre_test_state={"state_variable": state_var, "initial_value": "default"},
                post_test_state={"state_variable": state_var, "final_value": "updated"},
                dependencies=[],
                accessibility_checks=[],
                cleanup_actions=[]
            ),
            **_extract_traceability(strategy, edge_case)
        )


class ServiceTestCaseGenerator(BaseTestCaseGenerator):
    """Generates test cases for API client service dependency calls and fallbacks."""

    @property
    def category_name(self) -> str:
        return "Services"

    def supports(self, strategy: TestStrategy, edge_case: EdgeCaseScenario) -> bool:
        return (
            edge_case.category == "Services"
            and strategy.category in ("API/Service Interaction Tests", "Error Handling Tests")
        )

    def generate(self, strategy: TestStrategy, edge_case: EdgeCaseScenario) -> TestCase:
        test_data = dict(edge_case.input_data) if edge_case.input_data else {"service_mock": "http_success_200"}
        comp = strategy.target_component

        service_name = "AuthService"
        for token in strategy.id.split("-"):
            if "." in token:
                service_name = token.split(".")[0]
                break

        return TestCase(
            id=f"TC-{strategy.id}-{edge_case.id.replace('EC-' + strategy.id + '-', '')}",
            strategy_id=strategy.id,
            edge_case_id=edge_case.id,
            category=edge_case.category,
            priority=strategy.priority,
            component=comp,
            title=f"Service: {comp} - {edge_case.title}",
            objective=f"Validate service API calls and client behavior in '{comp}' for condition: '{edge_case.title}'.",
            preconditions=list(strategy.preconditions) + ["Mock HTTP interceptors are enabled"],
            steps=[
                f"Intersept and configure mocked service responses: {test_data}",
                f"Mount target component '{comp}'",
                "Invoke operational logic that triggers service/API calls",
                f"Verify service layer handles result and updates UI: '{edge_case.expected_behavior}'"
            ],
            test_data=test_data,
            expected_result=edge_case.expected_behavior,
            tags=list(strategy.coverage_tags) + list(edge_case.tags) + ["service", "api", "network"],
            metadata=TestCaseMetadata(
                component=comp,
                element="service_client",
                element_type="api_service",
                locator=TestCaseLocator(strategy="dependency_injection", value=service_name),
                action="invoke_api",
                assertion_type="http_status" if "SUCCESS" in strategy.id else "error_thrown",
                assertion_target="api_response",
                expected_value=edge_case.expected_behavior,
                mock_required=True,
                mock_services=[service_name],
                pre_test_state={"api_mocked": True},
                post_test_state={"api_called": True},
                dependencies=[service_name],
                accessibility_checks=[],
                cleanup_actions=["clear_mocks"]
            ),
            **_extract_traceability(strategy, edge_case)
        )


class RouteTestCaseGenerator(BaseTestCaseGenerator):
    """Generates test cases for router configuration and route guard validations."""

    @property
    def category_name(self) -> str:
        return "Routing"

    def supports(self, strategy: TestStrategy, edge_case: EdgeCaseScenario) -> bool:
        return edge_case.category == "Routing" and strategy.category == "Routing Tests"

    def generate(self, strategy: TestStrategy, edge_case: EdgeCaseScenario) -> TestCase:
        test_data = dict(edge_case.input_data) if edge_case.input_data else {"target_path": "/"}
        comp = strategy.target_component
        path_val = str(test_data.get("target_path", "/"))

        return TestCase(
            id=f"TC-{strategy.id}-{edge_case.id.replace('EC-' + strategy.id + '-', '')}",
            strategy_id=strategy.id,
            edge_case_id=edge_case.id,
            category=edge_case.category,
            priority=strategy.priority,
            component=comp,
            title=f"Routing: {comp} - {edge_case.title}",
            objective=f"Verify router behavior and guard constraints for: '{edge_case.title}'.",
            preconditions=list(strategy.preconditions) + ["Router mock configuration loaded"],
            steps=[
                "Configure router pathways and auth guards",
                f"Simulate navigation to destination using test payload parameters: {test_data}",
                "Check authentication status or param validity check results",
                f"Assert router redirects or displays target: '{edge_case.expected_behavior}'"
            ],
            test_data=test_data,
            expected_result=edge_case.expected_behavior,
            tags=list(strategy.coverage_tags) + list(edge_case.tags) + ["routing", "navigation"],
            metadata=TestCaseMetadata(
                component=comp,
                element="navigation",
                element_type="router",
                locator=TestCaseLocator(strategy="url_path", value=path_val),
                action="navigate",
                assertion_type="route_change",
                assertion_target="router_state",
                expected_value=edge_case.expected_behavior,
                mock_required=True,
                mock_services=["Router"],
                pre_test_state={"current_path": "/"},
                post_test_state={"current_path": path_val},
                dependencies=["Router"],
                accessibility_checks=[],
                cleanup_actions=[]
            ),
            **_extract_traceability(strategy, edge_case)
        )


class AccessibilityTestCaseGenerator(BaseTestCaseGenerator):
    """Generates test cases for ARIA properties, visual focus, and keyboard accessibility."""

    @property
    def category_name(self) -> str:
        return "Accessibility"

    def supports(self, strategy: TestStrategy, edge_case: EdgeCaseScenario) -> bool:
        return edge_case.category == "Accessibility" and strategy.category == "Accessibility Tests"

    def generate(self, strategy: TestStrategy, edge_case: EdgeCaseScenario) -> TestCase:
        test_data = dict(edge_case.input_data) if edge_case.input_data else {"a11y_standard": "WCAG2.1_AA"}
        comp = strategy.target_component

        checks = ["accessibility_compliance"]
        if "KEYBOARD" in edge_case.id.upper():
            checks = ["keyboard_navigation"]
        elif "FOCUS" in edge_case.id.upper():
            checks = ["focus_order"]
        elif "ARIA" in edge_case.id.upper():
            checks = ["aria_labels"]
        elif "SCREEN" in edge_case.id.upper():
            checks = ["screen_reader"]

        return TestCase(
            id=f"TC-{strategy.id}-{edge_case.id.replace('EC-' + strategy.id + '-', '')}",
            strategy_id=strategy.id,
            edge_case_id=edge_case.id,
            category=edge_case.category,
            priority=strategy.priority,
            component=comp,
            title=f"A11y: {comp} - {edge_case.title}",
            objective=f"Validate accessibility WCAG specs in '{comp}' for: '{edge_case.title}'.",
            preconditions=list(strategy.preconditions) + ["A11y checker tool is attached"],
            steps=[
                f"Render component '{comp}' in clean DOM context",
                f"Verify accessibility nodes using configurations: {test_data}",
                "Scan document for focus loops, screen reader labels, and color contrast",
                f"Verify check conforms to requirements: '{edge_case.expected_behavior}'"
            ],
            test_data=test_data,
            expected_result=edge_case.expected_behavior,
            tags=list(strategy.coverage_tags) + list(edge_case.tags) + ["accessibility", "a11y"],
            metadata=TestCaseMetadata(
                component=comp,
                element="dom_tree",
                element_type="accessibility_tree",
                locator=TestCaseLocator(strategy="accessibility_role", value="document"),
                action="audit",
                assertion_type="accessibility_standard",
                assertion_target="contrast_and_labels",
                expected_value="zero_violations",
                mock_required=False,
                mock_services=[],
                pre_test_state={},
                post_test_state={},
                dependencies=[],
                accessibility_checks=checks,
                cleanup_actions=[]
            ),
            **_extract_traceability(strategy, edge_case)
        )


def _build_default_test_case_registry() -> TestCaseRegistry:
    """Instantiate and populate the active concrete generators."""
    registry = TestCaseRegistry()
    registry.register(ComponentTestCaseGenerator())
    registry.register(FormTestCaseGenerator())
    registry.register(EventTestCaseGenerator())
    registry.register(StateTestCaseGenerator())
    registry.register(ServiceTestCaseGenerator())
    registry.register(RouteTestCaseGenerator())
    registry.register(AccessibilityTestCaseGenerator())
    return registry


def calculate_quality_score(tc: TestCase, strategy: TestStrategy, edge_case: EdgeCaseScenario, ir: FrameworkAgnosticIR | None) -> int:
    score = 100
    
    # 1. Objective validity
    if not tc.objective or len(tc.objective.strip()) < 15:
        score -= 20
    else:
        # Check for generic patterns
        generic_obj_patterns = ["satisfies expectation", "edge condition", "assert component", "perform interaction", "appropriate ui state", "no action occurs"]
        if any(pat in tc.objective.lower() for pat in generic_obj_patterns):
            score -= 10
            
    # 2. Exclude raw IDs or technical terms in primary fields (Rule 5)
    raw_id_patterns = ["ec-", "strat-", "tc-", "strategy_id", "edge_case_id", "ir-", "unmount", "teardown"]
    for field_val in [tc.title, tc.objective, tc.expected_result]:
        if any(pat in field_val.lower() for pat in raw_id_patterns):
            score -= 25
            
    # 3. Concrete action in steps
    generic_action_patterns = ["execute interaction", "perform action", "execute user interaction", "verify assertion target", "execute teardown", "perform operational logic", "dispatch event mock", "unmount", "teardown", "mock-reset", "cleanup"]
    for step in tc.steps:
        if any(pat in step.action.lower() or pat in step.expected.lower() for pat in generic_action_patterns):
            score -= 15
            
    # 4. expected_result validity
    if not tc.expected_result or len(tc.expected_result.strip()) < 10:
        score -= 20
    if tc.expected_result == "insufficient_test_information":
        score -= 60
    else:
        generic_expected_patterns = ["satisfies expectation", "verify target", "validate expectation", "expected behavior", "appropriate ui state", "no action occurs"]
        if any(pat in tc.expected_result.lower() for pat in generic_expected_patterns):
            score -= 20
            
    # 5. Component existence in IR (no hallucination)
    if not ir:
        score -= 20
    else:
        comp_names = {c.name for c in ir.components}
        if tc.component not in comp_names:
            # Component not found in current project's actual IR!
            logger.warning("Component '%s' not found in current project IR components: %s", tc.component, comp_names)
            score -= 60
            
    return max(0, min(100, score))


def enrich_and_validate_test_case(tc: TestCase, strategy: TestStrategy, edge_case: EdgeCaseScenario) -> TestCase:
    project_name = getattr(strategy, "project_name", None) or "IngestedProject"
    project_id = getattr(strategy, "project_id", None) or getattr(edge_case, "project_id", None)
    pipeline_run_id = getattr(strategy, "pipeline_run_id", None) or getattr(edge_case, "pipeline_run_id", None)
    
    tc.project_id = project_id
    tc.pipeline_run_id = pipeline_run_id
    tc.source_file = getattr(strategy, "source_file", None) or getattr(edge_case, "source_file", None)

    ir = get_cached_ir(pipeline_run_id or project_id or project_name)
        
    comp = strategy.target_component or tc.component or "DefaultComponent"
    tc.component = comp
    
    # Check if target component exists in IR components list
    comp_ir = None
    if ir:
        comp_ir = next((c for c in ir.components if c.name == comp), None)
        if comp_ir and comp_ir.file_path and not tc.source_file:
            tc.source_file = comp_ir.file_path
        
    # Check for insufficient information
    has_insufficient_info = False
    if not ir or not comp_ir:
        has_insufficient_info = True
        
    # Detect edge-case intent for Rule 8
    ec_id_lower = edge_case.id.lower()
    title_lower = edge_case.title.lower()
    category = tc.category
    
    is_disabled = "disabled" in ec_id_lower or "disabled" in title_lower
    is_rapid = "rapid" in ec_id_lower or "rapid" in title_lower
    is_api_success = ("api" in ec_id_lower or "service" in ec_id_lower) and ("success" in ec_id_lower or "success" in title_lower)
    is_api_failure = ("api" in ec_id_lower or "service" in ec_id_lower) and ("failure" in ec_id_lower or "error" in ec_id_lower or "failure" in title_lower or "error" in title_lower)
    is_input = "input" in ec_id_lower or "validation" in ec_id_lower or category == "Forms" or "input" in title_lower
    is_state = "state" in ec_id_lower or category == "State" or "state" in title_lower
        
    # 1. Clean Title and Wording
    title = f"{comp} {edge_case.title}"
    for raw_id in [strategy.id, edge_case.id, "EC-", "STRAT-", "TC-"]:
        title = title.replace(raw_id, "")
    title_clean = title.replace("-", " ").replace("_", " ").strip()
    title_words = title_clean.split()
    deduped_words = []
    for w in title_words:
        if not deduped_words or deduped_words[-1].lower() != w.lower():
            deduped_words.append(w)
    tc.title = " ".join(deduped_words)
    
    # Override custom titles based on exact examples
    if is_disabled:
        tc.title = "Disabled input does not trigger its handler"
    elif is_rapid:
        tc.title = f"Rapid interaction on trigger maintains component state"
    elif is_api_success:
        tc.title = f"Data displays successfully on service request completion"
    elif is_api_failure:
        tc.title = f"Layout displays error message banner on service request failure"
    elif is_input:
        tc.title = f"Form displays required validation messages for invalid submission"
    
    # 2. Objective (one sentence, clear behavior, no generic phrases)
    if is_disabled:
        tc.objective = "Verify that attempting to interact with a disabled field does not trigger the associated handler."
    elif is_rapid:
        tc.objective = "Verify that repeatedly triggering the interaction in rapid succession does not produce duplicate actions."
    elif is_api_success:
        tc.objective = "Verify that a successful API service response is processed and rendered correctly."
    elif is_api_failure:
        tc.objective = "Verify that an API service failure displays the appropriate error message."
    elif is_input:
        tc.objective = "Verify that submitting invalid data displays validation errors and blocks form submission."
    elif is_state:
        tc.objective = "Verify that triggering a state change updates the dependent visual elements correctly."
    elif category == "Routing":
        tc.objective = "Verify that navigation redirects to the target page according to guards."
    elif category == "Accessibility":
        tc.objective = "Verify that visual focus and role attributes conform to access standards."
    else:
        tc.objective = "Verify that the component handles initial rendering parameters and mounts successfully."

    # 3. Expected Result (one clear final observable result, no generic patterns)
    if has_insufficient_info:
        tc.expected_result = "insufficient_test_information"
    else:
        if is_disabled:
            tc.expected_result = "The disabled input does not accept the interaction and its handler is not triggered."
        elif is_rapid:
            tc.expected_result = "The component remains stable and only one action is executed during rapid interaction."
        elif is_api_success:
            tc.expected_result = "The API response data is loaded successfully and displayed in the UI."
        elif is_api_failure:
            tc.expected_result = "The application displays the appropriate error state and handles the API failure gracefully."
        elif is_input:
            tc.expected_result = "The form submission is prevented and the appropriate validation messages are displayed."
        elif is_state:
            tc.expected_result = "The internal state change successfully propagates to the rendered UI."
        elif category == "Routing":
            tc.expected_result = "The navigation transition resolves and routes to the target layout."
        elif category == "Accessibility":
            tc.expected_result = "The element focus and role attributes conform to accessibility criteria."
        else:
            tc.expected_result = "The component completes rendering and behaves as expected."

    # 4. Preconditions (Only conditions required before testing, clean)
    preconditions = []
    for pre in (tc.preconditions or []):
        pre_clean = pre.replace("-", " ").replace("_", " ").strip()
        if not any(x in pre_clean.lower() for x in ["mock", "simulator", "interceptor", "a11y", "unmount", "teardown"]):
            preconditions.append(pre_clean)
    if not preconditions:
        preconditions = [f"The component layout is available in the viewport."]
    tc.preconditions = preconditions

    # 5. Clean and Deduplicate Tags
    tags_set = set()
    for t in (tc.tags or []):
        t_clean = t.lower().strip()
        if not any(x in t_clean for x in ["ec-", "strat-", "tc-"]):
            if t_clean in ("forms", "form"):
                tags_set.add("form")
            elif t_clean in ("states", "state"):
                tags_set.add("state")
            elif t_clean in ("events", "event"):
                tags_set.add("event")
            elif t_clean in ("services", "service"):
                tags_set.add("service")
            elif t_clean in ("routing", "routes"):
                tags_set.add("routing")
            else:
                tags_set.add(t_clean)
    tc.tags = sorted(list(tags_set))

    # 6. Generate 4 structured steps: Action / Expected
    test_data_str = ", ".join([f"{k}: {v}" for k, v in tc.test_data.items()]) if tc.test_data else "none"
    
    steps = []
    if is_disabled:
        steps = [
            TestCaseStep(
                action="Open the form with the interactive fields disabled.",
                expected="The interactive controls are rendered in a disabled state."
            ),
            TestCaseStep(
                action="Attempt to enter text or click on the disabled fields.",
                expected="The fields do not receive focus and ignore the user inputs."
            ),
            TestCaseStep(
                action="Verify that the field value remains unchanged.",
                expected="No modifications are registered on the values."
            ),
            TestCaseStep(
                action="Verify that the change handler is not triggered.",
                expected="The associated event handler functions are not executed."
            )
        ]
    elif is_rapid:
        steps = [
            TestCaseStep(
                action="Open the component view containing the action trigger.",
                expected="The interactive trigger is displayed and active."
            ),
            TestCaseStep(
                action="Click the trigger multiple times in rapid succession.",
                expected="The interaction events are captured by the layout."
            ),
            TestCaseStep(
                action="Observe the component state and execution logs.",
                expected="Only a single action triggers and extra inputs are ignored or debounced."
            ),
            TestCaseStep(
                action="Check component stability.",
                expected="The component state remains stable and does not produce duplicate actions."
            )
        ]
    elif is_api_success:
        steps = [
            TestCaseStep(
                action="Configure mock services to return successful responses.",
                expected="The mock client is ready to receive requests."
            ),
            TestCaseStep(
                action="Trigger the component action demanding data loading.",
                expected="The network request is initiated to the server."
            ),
            TestCaseStep(
                action="Observe the visual indicators during payload resolution.",
                expected="A loading indicator displays while data is being resolved."
            ),
            TestCaseStep(
                action="Verify the rendered list items and labels.",
                expected="The loaded data is mapped successfully and rendered in the view layout."
            )
        ]
    elif is_api_failure:
        steps = [
            TestCaseStep(
                action="Configure mock services to return error responses.",
                expected="The mock client is set up to return a failure code."
            ),
            TestCaseStep(
                action="Trigger the component action demanding data loading.",
                expected="The request is initiated and the failure status is returned."
            ),
            TestCaseStep(
                action="Observe error fallback banners and labels in the layout.",
                expected="A clear error message banner is displayed in the UI."
            ),
            TestCaseStep(
                action="Check component interactivity.",
                expected="The view remains stable and enables retry actions."
            )
        ]
    elif is_input:
        controls_desc = "fields"
        if comp_ir and comp_ir.forms:
            ctrls = []
            for f in comp_ir.forms:
                ctrls.extend([c.name for c in f.controls])
            if ctrls:
                controls_desc = ", ".join([f"'{c}'" for c in list(set(ctrls))[:3]]) + " fields"
        steps = [
            TestCaseStep(
                action="Open the form view layout.",
                expected="All input controls are empty and visible."
            ),
            TestCaseStep(
                action=f"Enter invalid test values into the required {controls_desc}.",
                expected="The fields accept the invalid test inputs."
            ),
            TestCaseStep(
                action="Submit the form.",
                expected="The form submission is prevented."
            ),
            TestCaseStep(
                action="Observe the error messages under each form control.",
                expected="The appropriate validation messages are displayed."
            )
        ]
    elif is_state:
        steps = [
            TestCaseStep(
                action="Open the component view layout.",
                expected="Component renders in its default initial layout."
            ),
            TestCaseStep(
                action="Trigger the action that updates the internal state variables.",
                expected="Internal state properties mutate to reflect the update."
            ),
            TestCaseStep(
                action="Observe the visual indicators in the rendered UI.",
                expected="The state-dependent UI changes to the expected state."
            ),
            TestCaseStep(
                action="Verify target text values in the updated layout.",
                expected="All text and visual elements display the updated values."
            )
        ]
    elif category == "Routing":
        route_path = "/"
        if ir and ir.routes:
            route_path = ir.routes[0].path
        elif tc.metadata and tc.metadata.locator:
            route_path = tc.metadata.locator.value
        steps = [
            TestCaseStep(
                action="Configure router pathways and auth guards.",
                expected="Navigation router is prepared for path transitions."
            ),
            TestCaseStep(
                action=f"Simulate navigation to destination path '{route_path}'.",
                expected="Navigation controller resolves route guards."
            ),
            TestCaseStep(
                action="Check URL path status.",
                expected="URL location updates to the target destination path."
            ),
            TestCaseStep(
                action="Verify target component rendering.",
                expected="The view transitions to show the destination component layout."
            )
        ]
    elif category == "Accessibility":
        steps = [
            TestCaseStep(
                action="Render the component inside a clean test container.",
                expected="The DOM tree compiles successfully."
            ),
            TestCaseStep(
                action="Scan document landmarks and interactive nodes.",
                expected="ARIA properties and labels are present in the layout."
            ),
            TestCaseStep(
                action="Verify keyboard tab focus sequences.",
                expected="The focus outlines are visible and follow tab order."
            ),
            TestCaseStep(
                action="Run static accessibility contrast audit.",
                expected="The markup contrast conforms to accessibility standards."
            )
        ]
    else:
        steps = [
            TestCaseStep(
                action="Open the component layout view.",
                expected="Component mounts successfully in the test container."
            ),
            TestCaseStep(
                action="Inspect visual layout visual fields.",
                expected="Visual elements are present and match initial parameters."
            ),
            TestCaseStep(
                action="Verify visual structure tags and attributes.",
                expected="Markup tags and labels render safely."
            ),
            TestCaseStep(
                action="Observe component behavior.",
                expected="The component completes rendering successfully without crashes."
            )
        ]
        
    tc.steps = steps
    
    # 7. Function-Aware & Human-Readable Specifications
    target_fn = (
        getattr(strategy, "target_function", None)
        or getattr(edge_case, "target_function", None)
        or getattr(tc, "target_function", None)
    )
    
    if not target_fn or target_fn in ("render()", "render"):
        if ir and ir.components:
            comp_obj = next((c for c in ir.components if c.name == comp), None)
            if comp_obj:
                handlers = []
                for node in getattr(comp_obj, "interaction_graph", []) or []:
                    h = getattr(node, "handler", None)
                    if h and h not in handlers and h != "render()":
                        handlers.append(h)
                for form in getattr(comp_obj, "forms", []) or []:
                    sh = getattr(form, "submit_handler", None)
                    if sh and sh not in handlers:
                        handlers.append(sh)
                for oe in getattr(comp_obj, "outputs_events", []) or []:
                    h = oe.get("handler") or oe.get("name") if isinstance(oe, dict) else (getattr(oe, "handler", None) or getattr(oe, "name", None))
                    if h and h not in handlers:
                        handlers.append(h)
                for eh in getattr(comp_obj, "event_handlers", []) or []:
                    hname = getattr(eh, "name", None) or getattr(eh, "handler_name", None) or getattr(eh, "function", None)
                    if hname and hname not in handlers:
                        handlers.append(hname)
                for fn in getattr(comp_obj, "functions", []) or []:
                    fname = getattr(fn, "name", None)
                    if fname and fname not in handlers:
                        handlers.append(fname)
                if handlers:
                    t_lower = (tc.title + " " + tc.objective).lower()
                    matched = None

                    # Check metadata/element/state references first
                    search_terms = []
                    if tc.metadata and tc.metadata.element and tc.metadata.element != "interactive_element":
                        search_terms.append(tc.metadata.element.lower())
                    if edge_case and edge_case.element_id:
                        search_terms.append(edge_case.element_id.lower())
                    if strategy and strategy.element_id:
                        search_terms.append(strategy.element_id.lower())
                    if strategy and strategy.state_id:
                        search_terms.append(strategy.state_id.lower())
                    if edge_case and edge_case.state_id:
                        search_terms.append(edge_case.state_id.lower())

                    for term in search_terms:
                        for h in handlers:
                            if term in h.lower():
                                matched = h
                                break
                        if matched:
                            break

                    if not matched:
                        for h in handlers:
                            h_bare = h.removesuffix("()")
                            if h_bare.lower() in t_lower:
                                matched = h
                                break

                    if not matched:
                        if "form" in tc.category.lower() or "submit" in t_lower:
                            matched = next((h for h in handlers if "submit" in h.lower() or "form" in h.lower()), None)
                        elif "service" in tc.category.lower() or "api" in tc.category.lower():
                            matched = next((h for h in handlers if "fetch" in h.lower() or "api" in h.lower() or "load" in h.lower()), None)
                        elif "event" in tc.category.lower() or "click" in t_lower:
                            matched = next((h for h in handlers if "click" in h.lower() or "handle" in h.lower()), None)

                    if not matched:
                        matched = handlers[0] if handlers else "render()"

                    target_fn = matched

    if not target_fn:
        target_fn = "render()"

    if not target_fn.endswith("()"):
        target_fn = f"{target_fn}()"
    tc.target_function = target_fn

    if not tc.component_specification:
        tc.component_specification = (
            getattr(strategy, "behavior_reference", None)
            or f"{comp} provides interactive user interface presentation and executes {target_fn}."
        )

    if not tc.why_this_test_matters:
        tc.why_this_test_matters = (
            getattr(edge_case, "why_it_exists", None)
            or getattr(strategy, "reason", None)
            or f"Verifies that {target_fn} in {comp} handles scenario '{edge_case.title}' safely without runtime failures."
        )

    # Format human-readable behavior-driven title
    ec_title = edge_case.title
    if ":" in ec_title:
        ec_title = ec_title.split(":", 1)[1].strip()
    
    if target_fn and target_fn != "render()":
        tc.title = f"Verify {target_fn} handles {ec_title} in {comp}"
    else:
        tc.title = f"Verify {comp} renders correctly under {ec_title}"

    # Collapsed Technical Details Traceability Object
    tc.traceability = TestCaseTraceability(
        strategy_id=strategy.id,
        edge_case_id=edge_case.id,
        component_id=strategy.component_id or edge_case.component_id or comp,
        project_id=strategy.project_id or getattr(edge_case, "project_id", None) or getattr(tc, "project_id", None),
        pipeline_run_id=strategy.pipeline_run_id or getattr(edge_case, "pipeline_run_id", None) or getattr(tc, "pipeline_run_id", None),
        source_file=strategy.source_file or getattr(edge_case, "source_file", None) or getattr(tc, "source_file", None),
        element_id=strategy.element_id or edge_case.element_id,
        event_id=strategy.event_id or edge_case.event_id,
        state_id=strategy.state_id or edge_case.state_id,
        service_id=strategy.service_id or edge_case.service_id,
        route_id=strategy.route_id or edge_case.route_id,
        component=comp,
        function=target_fn,
        strategy=strategy.description or strategy.test_objective,
        edge_case=edge_case.title or edge_case.description,
    )
    
    # Calculate score
    tc.test_quality_score = calculate_quality_score(tc, strategy, edge_case, ir)
    
    return tc


class TestCaseGeneratorService:
    """Orchestrates structured test case generation from Strategy and Edge Case plans."""

    def __init__(self, registry: TestCaseRegistry | None = None) -> None:
        self._registry = registry or _build_default_test_case_registry()
        logger.info(
            "TestCaseGeneratorService initialised with %d generator(s)",
            len(self._registry.get_generators())
        )

    def generate_test_cases(
        self,
        strategy_plan: Union[TestCasePlanRequest, StrategyPlanResponse, Dict[str, Any]],
        edge_case_plan: Union[EdgeCasePlanResponse, Dict[str, Any], None] = None,
        frontend_context: Any = None,
    ) -> TestCasePlanResponse:
        """Core orchestrator: maps strategies and edge cases to generate structured test cases.

        Args:
            strategy_plan: TestCasePlanRequest, StrategyPlanResponse model, or raw dict.
            edge_case_plan: EdgeCasePlanResponse model, raw dict, or None if passed in request model.

        Returns:
            TestCasePlanResponse response object.

        Raises:
            ValueError: If validation fails.
        """
        logger.info("TestCaseGeneratorService: Starting test case generation process.")

        ec_plan_dict = {}

        # Normalize input Strategy plan
        if isinstance(strategy_plan, StrategyPlanResponse):
            strat_plan_dict = strategy_plan.model_dump()
        elif hasattr(strategy_plan, "strategy_plan") and getattr(strategy_plan, "strategy_plan"):
            # Legacy object wrapper support
            legacy_sp = getattr(strategy_plan, "strategy_plan")
            strat_plan_dict = legacy_sp.model_dump() if hasattr(legacy_sp, "model_dump") else legacy_sp
            legacy_ec = getattr(strategy_plan, "edge_case_plan", None)
            if legacy_ec:
                ec_plan_dict = legacy_ec.model_dump() if hasattr(legacy_ec, "model_dump") else legacy_ec
        elif isinstance(strategy_plan, dict):
            if "ir" in strategy_plan and strategy_plan["ir"]:
                from app.models.ir_models import FrameworkAgnosticIR
                from app.utils.ir_cache import cache_ir
                try:
                    cached_ir_obj = FrameworkAgnosticIR.model_validate(strategy_plan["ir"])
                    cache_ir(cached_ir_obj)
                except Exception:
                    pass
            if "strategy_plan" in strategy_plan:
                strat_plan_dict = strategy_plan["strategy_plan"]
                ec_plan_dict = strategy_plan.get("edge_case_plan", {})
            else:
                strat_plan_dict = strategy_plan
        else:
            raise ValueError("strategy_plan must be a StrategyPlanResponse or dict.")

        # Normalize input Edge Case plan if passed explicitly
        if edge_case_plan is not None:
            if isinstance(edge_case_plan, EdgeCasePlanResponse):
                ec_plan_dict = edge_case_plan.model_dump()
            elif isinstance(edge_case_plan, dict):
                ec_plan_dict = edge_case_plan
            else:
                raise ValueError("edge_case_plan must be an EdgeCasePlanResponse or dict.")

        project_name = strat_plan_dict.get("project_name", "IngestedProject")
        project_id = strat_plan_dict.get("project_id") or ec_plan_dict.get("project_id")
        pipeline_run_id = strat_plan_dict.get("pipeline_run_id") or ec_plan_dict.get("pipeline_run_id")
        framework = strat_plan_dict.get("framework", "Unknown")

        # Retrieve current project's IR for validation
        from app.utils.ir_cache import get_cached_ir
        current_ir = get_cached_ir(pipeline_run_id or project_id or project_name)
        valid_component_names = {c.name for c in current_ir.components} if current_ir and current_ir.components else set()

        _bridge_scenarios_cache = []
        if frontend_context:
            try:
                from app.services.frontend_context.behavior_context_bridge import BehaviorContextBridge
                _bridge_scenarios_cache = BehaviorContextBridge().generate_scenarios(frontend_context)
            except Exception as exc:
                logger.warning("Could not pre-generate bridge scenarios: %s", exc)

        # Parse internal lists to Pydantic objects safely
        from app.models.strategy_models import TestStrategy
        from app.models.edge_case_models import EdgeCaseScenario

        strategies: List[TestStrategy] = []
        for s_dict in strat_plan_dict.get("strategies", []):
            st_obj = TestStrategy.model_validate(s_dict)
            if not st_obj.project_id and project_id:
                st_obj.project_id = project_id
            if not st_obj.pipeline_run_id and pipeline_run_id:
                st_obj.pipeline_run_id = pipeline_run_id
            strategies.append(st_obj)

        edge_cases: List[EdgeCaseScenario] = []
        if not ec_plan_dict or not ec_plan_dict.get("edge_cases"):
            # Reconstruct edge cases from strategy_plan
            reconstructed_edge_cases = []
            for s_dict in strat_plan_dict.get("strategies", []):
                s_id = s_dict.get("id", "")
                if s_id.startswith("EC-"):
                    strat_ref = s_dict.get("strategy_id") or ""
                    prefix = f"EC-{strat_ref}-"
                    code = s_id.replace(prefix, "") if strat_ref else "EDGE"
                    
                    category = "State"
                    s_cat = s_dict.get("category", "")
                    if "form" in s_cat.lower():
                        category = "Forms"
                    elif "event" in s_cat.lower() or "user" in s_cat.lower():
                        category = "Events"
                    elif "state" in s_cat.lower() or "hook" in s_cat.lower():
                        category = "State"
                    elif "api" in s_cat.lower() or "service" in s_cat.lower() or "error" in s_cat.lower():
                        category = "Services"
                    elif "route" in s_cat.lower() or "navigation" in s_cat.lower():
                        category = "Routing"
                    elif "access" in s_cat.lower() or "a11y" in s_cat.lower():
                        category = "Accessibility"

                    reconstructed_edge_cases.append(
                        EdgeCaseScenario(
                            id=s_id,
                            strategy_id=strat_ref,
                            category=category,
                            priority=s_dict.get("priority", "Medium"),
                            title=s_dict.get("test_objective") or s_dict.get("description", "Edge Case"),
                            description=s_dict.get("description", ""),
                            input_data={"element_id": s_dict.get("element_id")} if s_dict.get("element_id") else {},
                            expected_behavior=s_dict.get("expected_outcome") or s_dict.get("description", ""),
                            tags=s_dict.get("coverage_tags", []),
                            project_id=project_id,
                            pipeline_run_id=pipeline_run_id,
                            source_file=s_dict.get("source_file"),
                            component_id=s_dict.get("component_id"),
                            element_id=s_dict.get("element_id"),
                            event_id=s_dict.get("event_id"),
                            state_id=s_dict.get("state_id"),
                            service_id=s_dict.get("service_id"),
                            route_id=s_dict.get("route_id"),
                            edge_case_type=code,
                            assertions=[s_dict.get("reason")] if s_dict.get("reason") else [],
                            locator_rtl="container.querySelector('div')",
                            locator_angular="by.css('div')",
                            jest_matcher="toBeInTheDocument",
                            mock_requirements=s_dict.get("preconditions", []),
                            expected_state_changes={},
                            expected_dom_changes=[s_dict.get("expected_outcome")] if s_dict.get("expected_outcome") else [],
                            why_it_exists=s_dict.get("reason", ""),
                            what_behavior_it_validates=s_dict.get("behavior_reference", ""),
                            what_failure_it_prevents=s_dict.get("expected_outcome", "")
                        )
                    )
            edge_cases.extend(reconstructed_edge_cases)
        else:
            for ec_dict in ec_plan_dict.get("edge_cases", []):
                ec_obj = EdgeCaseScenario.model_validate(ec_dict)
                if not ec_obj.project_id and project_id:
                    ec_obj.project_id = project_id
                if not ec_obj.pipeline_run_id and pipeline_run_id:
                    ec_obj.pipeline_run_id = pipeline_run_id
                edge_cases.append(ec_obj)

        # Map by ID for quick lookup
        generated_cases: List[TestCase] = []

        # Attempt Hybrid Groq LLM Test Case Generation (Module 7 LLM Layer)
        try:
            from app.services.test_case_generator.llm_test_case_generator import LLMTestCaseGenerator
            llm_gen = LLMTestCaseGenerator()
            llm_cases = llm_gen.generate_llm_test_cases(
                strategy_plan=StrategyPlanResponse(strategies=strategies, project_id=project_id, pipeline_run_id=pipeline_run_id),
                edge_case_plan=EdgeCasePlanResponse(edge_cases=edge_cases, project_id=project_id, pipeline_run_id=pipeline_run_id),
                frontend_context=frontend_context,
            )
            if llm_cases:
                for tc in llm_cases:
                    tc.project_id = project_id
                    tc.pipeline_run_id = pipeline_run_id
                    generated_cases.append(tc)
                logger.info("Hybrid LLM Layer (Module 7): Inserted %d LLM-reasoned test cases.", len(llm_cases))
        except Exception as exc:
            logger.warning("Hybrid LLM Layer (Module 7): LLM test case generation skipped/fallback: %s", exc)

        strategy_map = {s.id: s for s in strategies}

        # Worker for parallel execution
        def _process_edge_case(generator: Any, ec: EdgeCaseScenario) -> Optional[TestCase]:
            strat = strategy_map.get(ec.strategy_id)
            if not strat or not generator.supports(strat, ec):
                return None
            try:
                tc = generator.generate(strat, ec)
                tc = enrich_and_validate_test_case(tc, strat, ec)
                tc.project_id = strat.project_id or ec.project_id or project_id
                tc.pipeline_run_id = strat.pipeline_run_id or ec.pipeline_run_id or pipeline_run_id
                tc.source_file = strat.source_file or ec.source_file or tc.source_file
                tc.risk = getattr(strat, 'risk', f"{tc.priority} (1/10)") or f"{tc.priority} (1/10)"
                tc.mock_requirements = getattr(ec, 'mock_requirements', []) or tc.metadata.mock_services
                tc.expected_dom_changes = getattr(ec, 'expected_dom_changes', []) or [f"DOM node updated for {tc.component}"]
                tc.expected_state_changes = getattr(ec, 'expected_state_changes', {}) or tc.metadata.post_test_state
                tc.expected_accessibility_behavior = "Ensure element has accessible role, label, and keyboard focus compliance." if "a11y" in tc.category.lower() or "accessibility" in tc.category.lower() else "Standard DOM accessibility layout."
                tc.expected_side_effects = getattr(ec, 'assertions', []) or [f"Callback/event side-effect for {tc.metadata.action}"]

                # Deterministic validation: reject test case if component is not in current project inventory
                if valid_component_names and tc.component not in valid_component_names:
                    logger.warning(
                        "REJECTING test case %s: component '%s' not present in current project inventory %s",
                        tc.id,
                        tc.component,
                        valid_component_names,
                    )
                    return None

                if tc.test_quality_score >= 80:
                    return tc
                else:
                    logger.warning("Rejecting test case %s due to low quality score %d", tc.id, tc.test_quality_score)
                    return None
            except Exception as exc:
                logger.error("Failed to generate test case for strategy %s, edge case %s: %s", ec.strategy_id, ec.id, exc)
                return None

        # Run generators using parallel thread pool execution
        import concurrent.futures
        for generator in self._registry.get_generators():
            logger.info("Running Test Case Generator (parallelized): %s", generator.__class__.__name__)
            with concurrent.futures.ThreadPoolExecutor(max_workers=min(10, max(1, len(edge_cases)))) as executor:
                futures = [executor.submit(_process_edge_case, generator, ec) for ec in edge_cases]
                for future in concurrent.futures.as_completed(futures):
                    res_tc = future.result()
                    if res_tc:
                        generated_cases.append(res_tc)

        # Synthesize deep function-aware test cases for any handlers discovered in IR
        if current_ir and current_ir.components:
            base_strat = strategies[0] if strategies else None
            base_ec = edge_cases[0] if edge_cases else None
            if base_strat and base_ec:
                for comp_obj in current_ir.components:
                    comp_name = comp_obj.name
                    handlers: List[str] = []

                    # 1. From interaction_graph
                    for node in getattr(comp_obj, "interaction_graph", []) or []:
                        h = getattr(node, "handler", None)
                        if h and h not in handlers and h != "render()":
                            handlers.append(h)

                    # 2. From forms
                    for form in getattr(comp_obj, "forms", []) or []:
                        sh = getattr(form, "submit_handler", None)
                        if sh and sh not in handlers:
                            handlers.append(sh)

                    # 3. From outputs_events
                    for oe in getattr(comp_obj, "outputs_events", []) or []:
                        h = oe.get("handler") or oe.get("name") if isinstance(oe, dict) else (getattr(oe, "handler", None) or getattr(oe, "name", None))
                        if h and h not in handlers:
                            handlers.append(h)

                    # 4. From event_handlers / functions
                    for eh in getattr(comp_obj, "event_handlers", []) or []:
                        hname = getattr(eh, "name", None) or getattr(eh, "handler_name", None) or getattr(eh, "function", None)
                        if hname and hname not in handlers:
                            handlers.append(hname)

                    for fn in getattr(comp_obj, "functions", []) or []:
                        fname = getattr(fn, "name", None) if not isinstance(fn, dict) else fn.get("name")
                        if fname and fname not in handlers:
                            handlers.append(fname)

                    # 5. From FrontendContext if available
                    try:
                        from app.services.frontend_context.file_analyzer import _context_cache
                        for c_key, fce_ctx in _context_cache.items():
                            if fce_ctx.component_name == comp_name:
                                for f_item in fce_ctx.functions:
                                    if f_item.name and f_item.name not in handlers:
                                        handlers.append(f_item.name)
                                for e_item in fce_ctx.events:
                                    h_name = e_item.handler or e_item.name
                                    if h_name and h_name not in handlers:
                                        handlers.append(h_name)
                    except Exception:
                        pass

                    # Check mapped functions for this component in generated_cases
                    covered_fn_for_comp = {c.target_function.removesuffix("()") for c in generated_cases if c.component == comp_name and c.target_function}

                    for fn_raw in handlers:
                        fn_bare = fn_raw.removesuffix("()")
                        if fn_bare not in covered_fn_for_comp:
                            fn_formatted = f"{fn_bare}()"
                            cat = "Forms" if "submit" in fn_bare.lower() else ("Events" if "change" in fn_bare.lower() or "click" in fn_bare.lower() else "State")

                            # --- Behavior-aware title/objective/steps from bridge scenarios ---
                            matched_scenario = None
                            if _bridge_scenarios_cache:
                                matched_scenario = next(
                                    (sc for sc in _bridge_scenarios_cache
                                     if sc.get("component") == comp_name and sc.get("function") == fn_bare),
                                    None,
                                )

                            if matched_scenario:
                                t_title = matched_scenario["test_title"]
                                t_objective = matched_scenario["test_objective"]
                                t_preconditions = matched_scenario.get("preconditions", ["DOM testing environment initialized", f"Mount component {comp_name}"])
                                t_steps = [
                                    TestCaseStep(action=s["action"], expected=s["expected"])
                                    for s in matched_scenario.get("steps", [])
                                ] or [
                                    TestCaseStep(action=f"Mount component '{comp_name}'", expected="Component renders successfully"),
                                    TestCaseStep(action=f"Invoke handler function '{fn_formatted}'", expected=f"State updates for {fn_formatted}"),
                                    TestCaseStep(action=f"Verify component cleanup after '{fn_formatted}'", expected="Component unmounts cleanly"),
                                ]
                                t_expected_result = matched_scenario.get("expected_result", f"{fn_formatted} completes execution without errors.")
                                t_why = matched_scenario.get("why_this_test_matters", f"Verifies that function {fn_formatted} in {comp_name} handles execution cleanly.")
                                cat = matched_scenario.get("category", cat)
                            else:
                                # Keyword-based fallback titles
                                if "email" in fn_bare.lower():
                                    t_title = f"Verify email state updates when {fn_bare} receives a new value"
                                elif "password" in fn_bare.lower():
                                    t_title = f"Verify password state updates when {fn_bare} receives a new value"
                                elif "remember" in fn_bare.lower():
                                    t_title = f"Verify rememberMe state updates when {fn_bare} receives a toggle event"
                                elif "submit" in fn_bare.lower():
                                    t_title = f"Verify {fn_bare} prevents default form submission and submits credentials"
                                elif "toggle" in fn_bare.lower():
                                    t_title = f"Verify {fn_bare} toggles state between true and false in {comp_name}"
                                elif "save" in fn_bare.lower():
                                    t_title = f"Verify {fn_bare} persists changes and updates state in {comp_name}"
                                elif "delete" in fn_bare.lower() or "remove" in fn_bare.lower():
                                    t_title = f"Verify {fn_bare} removes item and updates state in {comp_name}"
                                elif "logout" in fn_bare.lower() or "signout" in fn_bare.lower():
                                    t_title = f"Verify {fn_bare} triggers logout callback in {comp_name}"
                                elif "close" in fn_bare.lower() or "dismiss" in fn_bare.lower():
                                    t_title = f"Verify {fn_bare} dismisses modal or overlay in {comp_name}"
                                elif "open" in fn_bare.lower() or "show" in fn_bare.lower():
                                    t_title = f"Verify {fn_bare} opens modal or reveals hidden content in {comp_name}"
                                elif "change" in fn_bare.lower():
                                    t_title = f"Verify {fn_bare} updates associated state from user input in {comp_name}"
                                elif "click" in fn_bare.lower():
                                    t_title = f"Verify {fn_bare} triggers expected action on click in {comp_name}"
                                elif "fetch" in fn_bare.lower() or "load" in fn_bare.lower():
                                    t_title = f"Verify {fn_bare} fetches data and updates component state in {comp_name}"
                                else:
                                    t_title = f"Verify {fn_formatted} executes handler logic safely in {comp_name}"

                                t_objective = f"Verify that {fn_formatted} in {comp_name} executes state transitions and side effects safely."
                                t_preconditions = ["DOM testing environment initialized", f"Mount component {comp_name}"]
                                t_steps = [
                                    TestCaseStep(action=f"Mount component '{comp_name}'", expected="Component renders successfully"),
                                    TestCaseStep(action=f"Inspect initial DOM tree state for '{comp_name}'", expected="DOM node elements are mounted"),
                                    TestCaseStep(action=f"Invoke handler function '{fn_formatted}'", expected=f"State and DOM update appropriately for {fn_formatted}"),
                                    TestCaseStep(action=f"Verify component cleanup after '{fn_formatted}'", expected="Component unmounts cleanly without memory leaks"),
                                ]
                                t_expected_result = f"{fn_formatted} completes execution without errors."
                                t_why = f"Verifies that function {fn_formatted} in {comp_name} handles execution cleanly without throwing runtime exceptions."

                            fn_tc = TestCase(
                                id=f"TC-{comp_name.upper()}-{fn_bare.upper()}-001",
                                strategy_id=base_strat.id,
                                edge_case_id=base_ec.id,
                                category=cat,
                                priority="High",
                                component=comp_name,
                                title=t_title,
                                objective=t_objective,
                                preconditions=t_preconditions,
                                steps=t_steps,
                                test_data={"handler": fn_bare},
                                expected_result=t_expected_result,
                                tags=[cat.lower(), "function_behavior", comp_name],
                                metadata=TestCaseMetadata(
                                    component=comp_name,
                                    element=fn_bare,
                                    element_type="function",
                                    locator=TestCaseLocator(strategy="handler", value=fn_bare),
                                    action="invoke",
                                    assertion_type="callback_triggered",
                                    assertion_target=fn_formatted,
                                    expected_value="success",
                                ),
                                component_specification=f"{comp_name} provides interactive component logic and handles {fn_formatted}.",
                                target_function=fn_formatted,
                                why_this_test_matters=t_why,
                                project_id=project_id,
                                pipeline_run_id=pipeline_run_id,
                                source_file=getattr(comp_obj, "file_path", None) or f"src/{comp_name}.jsx",
                            )
                            fn_tc.traceability = TestCaseTraceability(
                                strategy_id=base_strat.id,
                                edge_case_id=base_ec.id,
                                component_id=f"comp_{comp_name}",
                                project_id=project_id,
                                pipeline_run_id=pipeline_run_id,
                                source_file=getattr(comp_obj, "file_path", None) or f"src/{comp_name}.jsx",
                                component=comp_name,
                                function=fn_formatted,
                                strategy=base_strat.description,
                                edge_case=base_ec.title,
                            )
                            fn_tc.test_quality_score = 95
                            generated_cases.append(fn_tc)

        # =====================================================================
        # Behavior-driven test case generation from BehaviorContextBridge
        # =====================================================================
        if frontend_context and base_strat and base_ec:
            try:
                from app.services.frontend_context.behavior_context_bridge import BehaviorContextBridge
                bridge = BehaviorContextBridge()
                bridge_scenarios = bridge.generate_scenarios(frontend_context)
                logger.info(
                    "BehaviorContextBridge: %d behavior scenarios generated for behavior-driven test cases",
                    len(bridge_scenarios),
                )

                # Build set of already-covered (component, function) pairs
                covered_comp_fn = {
                    (tc.component, tc.target_function.removesuffix("()"))
                    for tc in generated_cases
                    if tc.target_function
                }

                for sc_idx, scenario in enumerate(bridge_scenarios):
                    sc_comp = scenario.get("component", "")
                    sc_fn = scenario.get("function", "")

                    # Skip if already covered by strategy/edge-case or IR-synthesized handlers
                    if (sc_comp, sc_fn) in covered_comp_fn:
                        continue

                    # Skip if component is not in this project's inventory
                    if valid_component_names and sc_comp not in valid_component_names:
                        continue

                    sc_steps = [
                        TestCaseStep(action=s.get("action", ""), expected=s.get("expected", ""))
                        for s in scenario.get("steps", [])
                    ] or [
                        TestCaseStep(action=f"Mount component '{sc_comp}'", expected="Component renders"),
                        TestCaseStep(action=f"Invoke {sc_fn}()", expected="Handler executes"),
                    ]

                    sc_tc = TestCase(
                        id=f"TC-BHV-{sc_comp.upper()}-{sc_fn.upper()}-{sc_idx+1:03d}",
                        strategy_id=base_strat.id,
                        edge_case_id=base_ec.id,
                        category=scenario.get("category", "State"),
                        priority="High",
                        component=sc_comp,
                        title=scenario.get("test_title", f"Verify {sc_fn}() in {sc_comp}"),
                        objective=scenario.get("test_objective", f"Verify {sc_fn}() behavior in {sc_comp}."),
                        preconditions=scenario.get("preconditions", [f"Mount {sc_comp}"]),
                        steps=sc_steps,
                        test_data={"handler": sc_fn, "trigger": scenario.get("trigger", ""), "behavior": scenario.get("behavior", "")},
                        expected_result=scenario.get("expected_result", f"{sc_fn}() completes."),
                        tags=[scenario.get("category", "state").lower(), "behavior_driven", sc_comp],
                        metadata=TestCaseMetadata(
                            component=sc_comp,
                            element=sc_fn,
                            element_type="function",
                            locator=TestCaseLocator(strategy="handler", value=sc_fn),
                            action="invoke",
                            assertion_type="state_change",
                            assertion_target=f"{sc_fn}()",
                            expected_value="success",
                        ),
                        component_specification=f"{sc_comp} handles {sc_fn}() via {scenario.get('trigger', 'trigger')}.",
                        target_function=f"{sc_fn}()",
                        why_this_test_matters=scenario.get("why_this_test_matters", f"Validates {sc_fn}() behavior in {sc_comp}."),
                        project_id=project_id,
                        pipeline_run_id=pipeline_run_id,
                        source_file=scenario.get("source_file", f"src/{sc_comp}.jsx"),
                    )
                    sc_tc.traceability = TestCaseTraceability(
                        strategy_id=base_strat.id,
                        edge_case_id=base_ec.id,
                        component_id=f"comp_{sc_comp}",
                        project_id=project_id,
                        pipeline_run_id=pipeline_run_id,
                        source_file=scenario.get("source_file") or (f"src/app/{sc_comp}/{sc_comp}.component.ts" if (framework or "").lower() == "angular" else f"src/{sc_comp}.jsx"),
                        component=sc_comp,
                        function=f"{sc_fn}()",
                        strategy=base_strat.description,
                        edge_case=base_ec.title,
                    )
                    sc_tc.test_quality_score = 97
                    generated_cases.append(sc_tc)
                    covered_comp_fn.add((sc_comp, sc_fn))

            except Exception as exc:
                logger.warning(
                    "BehaviorContextBridge: Failed to generate behavior-driven test cases: %s. "
                    "Falling back to existing pipeline.",
                    exc,
                )

        # Deduplicate cases
        unique_cases = self._deduplicate_test_cases(generated_cases)

        # Validate
        self.validate_test_cases(unique_cases, strategies, edge_cases)

        # Compute coverage summary report
        comp_set = set(tc.component for tc in unique_cases)
        fn_set = set(tc.target_function for tc in unique_cases if tc.target_function)
        
        coverage_matrix: Dict[str, Dict[str, int]] = {}
        for tc in unique_cases:
            comp = tc.component
            fn = tc.target_function or "render()"
            if comp not in coverage_matrix:
                coverage_matrix[comp] = {}
            coverage_matrix[comp][fn] = coverage_matrix[comp].get(fn, 0) + 1

        cov_summary = {
            "components_discovered": len(valid_component_names) or len(comp_set),
            "functions_discovered": len(fn_set),
            "behaviors_identified": len(strategies),
            "test_cases_generated": len(unique_cases),
            "duplicates_removed": max(0, len(generated_cases) - len(unique_cases)),
            "coverage_matrix": coverage_matrix,
        }

        logger.info(
            "TestCaseGeneratorService: Completed. Total test cases: %d (project_id=%s). Components=%d, Functions=%d",
            len(unique_cases),
            project_id,
            cov_summary["components_discovered"],
            cov_summary["functions_discovered"],
        )

        return TestCasePlanResponse(
            project_name=project_name,
            project_id=project_id,
            pipeline_run_id=pipeline_run_id,
            framework=framework,
            total_test_cases=len(unique_cases),
            test_cases=unique_cases,
            coverage_summary=cov_summary
        )

    def _deduplicate_test_cases(self, test_cases: List[TestCase]) -> List[TestCase]:
        """Remove duplicate test cases based on unique ID, core metadata fields, and semantic similarity."""
        seen_ids: Set[str] = set()
        seen_semantic_keys: Set[str] = set()
        unique: List[TestCase] = []
        duplicates_count = 0

        # Helper to normalize string for semantic similarity
        def normalize_string(s: str) -> str:
            if not s:
                return ""
            # Lowercase, remove common punctuation, sort words to be order-independent
            words = [w.strip(".,;:!?-'\"()[]{}") for w in s.lower().split()]
            return " ".join(sorted([w for w in words if w]))

        for tc in test_cases:
            # Exact check
            if tc.id in seen_ids:
                duplicates_count += 1
                logger.info("Removing exact duplicate test case ID: %s", tc.id)
                continue
            
            # Semantic composite check: component + target_function + category + normalized title/objective/expected_result
            norm_title = normalize_string(tc.title)
            norm_obj = normalize_string(tc.objective)
            norm_exp = normalize_string(tc.expected_result)
            
            semantic_key = f"{tc.component}:{tc.target_function}:{tc.category}:{norm_title}:{norm_obj}:{norm_exp}"

            if semantic_key in seen_semantic_keys:
                duplicates_count += 1
                logger.info("Removing semantic duplicate test case: ID='%s', Component='%s', Target='%s'", tc.id, tc.component, tc.target_function)
            else:
                seen_ids.add(tc.id)
                seen_semantic_keys.add(semantic_key)
                unique.append(tc)

        if duplicates_count > 0:
            logger.info("Duplicate test case removal: removed %d duplicate(s)", duplicates_count)

        return unique

    def validate_test_cases(
        self,
        test_cases: List[TestCase],
        strategies: List[TestStrategy],
        edge_cases: List[EdgeCaseScenario]
    ) -> None:
        """Validates all generated test cases against business rules."""
        logger.info("TestCaseGeneratorService: Validating %d test case(s)", len(test_cases))

        known_strategy_ids = {s.id for s in strategies}
        known_edge_case_ids = {ec.id for ec in edge_cases}

        valid_priorities = {"high", "medium", "low"}
        seen_ids = set()

        for tc in test_cases:
            # 1. Duplicate ID check
            if tc.id in seen_ids:
                msg = f"Validation Error: Duplicate Test Case ID found: {tc.id}"
                logger.error(msg)
                raise ValueError(msg)
            seen_ids.add(tc.id)

            # 2. Invalid Strategy Reference
            if tc.strategy_id not in known_strategy_ids:
                msg = f"Validation Error: Test case '{tc.id}' references unknown Strategy ID '{tc.strategy_id}'."
                logger.error(msg)
                raise ValueError(msg)

            # 3. Invalid Edge Case Reference
            if tc.edge_case_id not in known_edge_case_ids:
                msg = f"Validation Error: Test case '{tc.id}' references unknown Edge Case ID '{tc.edge_case_id}'."
                logger.error(msg)
                raise ValueError(msg)

            # 4. Missing Steps
            if not tc.steps:
                msg = f"Validation Error: Test case '{tc.id}' has empty steps list."
                logger.error(msg)
                raise ValueError(msg)

            # 5. Missing Expected Result
            if not tc.expected_result or not tc.expected_result.strip():
                msg = f"Validation Error: Test case '{tc.id}' is missing expected_result description."
                logger.error(msg)
                raise ValueError(msg)

            # 6. Invalid Priority check
            if tc.priority.lower() not in valid_priorities:
                msg = f"Validation Error: Test case '{tc.id}' has invalid priority level '{tc.priority}'."
                logger.error(msg)
                raise ValueError(msg)

            # 7. Empty Test Data check
            if not tc.test_data:
                msg = f"Validation Error: Test case '{tc.id}' has empty test_data dict."
                logger.error(msg)
                raise ValueError(msg)

        logger.info("TestCaseGeneratorService: Validation passed successfully.")
