"""
Concrete Edge Case Generators – Module 6.

Implements IR-aware generators for:
- FormEdgeCaseGenerator
- EventEdgeCaseGenerator
- StateEdgeCaseGenerator
- ServiceEdgeCaseGenerator
- RouteEdgeCaseGenerator
- AccessibilityEdgeCaseGenerator
- PropEdgeCaseGenerator [NEW]
"""

import logging
from typing import List, Dict, Any, Optional
from app.models.strategy_models import TestStrategy
from app.models.edge_case_models import EdgeCaseScenario
from app.services.edge_case_generator.base_generator import BaseEdgeCaseGenerator
from app.utils.ir_cache import get_cached_ir

logger = logging.getLogger(__name__)


def get_dynamic_priority(comp_name: str, base_priority: str = "Medium") -> str:
    """Scale edge case priority dynamically using component risk score."""
    ir = get_cached_ir()
    if not ir:
        return base_priority

    comp = next((c for c in ir.components if c.name == comp_name), None)
    if comp and comp.risk_score:
        score = comp.risk_score
        if score >= 5.0:
            return "High"
        elif score >= 3.0:
            return "Medium"
        else:
            return "Low"
    return base_priority


class FormEdgeCaseGenerator(BaseEdgeCaseGenerator):
    """Generates edge cases for Form Validation categories."""

    @property
    def category_name(self) -> str:
        return "Forms"

    def supports(self, strategy: TestStrategy) -> bool:
        ir = get_cached_ir()
        comp_name = strategy.target_component
        
        # Check if form exists for this component in IR
        if ir:
            comp = next((c for c in ir.components if c.name == comp_name), None)
            if comp and not comp.forms:
                return False
        
        return "FORM" in strategy.id or strategy.category == "Form Validation Tests"

    def generate(self, strategy: TestStrategy) -> List[EdgeCaseScenario]:
        strat_id = strategy.id
        target = strategy.target_component
        comp_id = strategy.component_id or f"comp_{target}"
        form_id = strategy.element_id
        edge_cases = []

        ir = get_cached_ir()
        form_meta = None
        if ir and form_id:
            form_meta = next((f for f in ir.forms if f.id == form_id or f.component_name == target), None)
        
        priority = get_dynamic_priority(target, "High")

        scenarios = [
            ("EMPTY-INPUT", "Empty Input", "Submit form with empty fields", "Form validation should block submission and highlight required fields."),
            ("INVALID-FORMAT", "Invalid Input", "Submit form with malformed email or input values", "Verify invalid format indicators are visible in DOM."),
            ("MIN-LENGTH", "Min Length", "Submit text input below minimum character boundary", "Verify character length error warning."),
            ("MAX-LENGTH", "Max Length", "Submit input exceeding maximum length limits", "Verify input character limits or truncation behaves gracefully."),
            ("BOUNDARY-VALUES", "Boundary Values", "Submit boundary values (0, max boundary) on numeric inputs", "Form handles numeric constraints correctly."),
            ("SUBMIT-INVALID", "Submit", "Trigger form submission with invalid inputs active", "Submission is blocked; errors are displayed."),
            ("RESET", "Reset", "Populate fields and trigger form reset button", "Verify all input fields are reset to default states."),
        ]

        # Conditional controlled/uncontrolled inputs edge case if form metadata exists
        if form_meta:
            scenarios.append((
                "CONTROL-BINDING",
                "Controlled/Uncontrolled Inputs",
                "Simulate rapid input typing and value binding checks",
                "Verify state updates and field UI synchronize correctly."
            ))

        for idx, (code, case_type, desc, expected) in enumerate(scenarios):
            ec_id = f"EC-{strat_id}-{code}"
            
            rtl_loc = f"screen.getByRole('form')" if form_meta else "container.querySelector('form')"
            ang_loc = f"by.css('form')"

            edge_cases.append(
                EdgeCaseScenario(
                    id=ec_id,
                    strategy_id=strat_id,
                    category=self.category_name,
                    priority=priority,
                    title=f"Form: {case_type}",
                    description=f"Validate that '{target}' handles form case: {desc.lower()}.",
                    input_data={"form_id": form_id},
                    expected_behavior=expected,
                    tags=["forms", "validation", code.lower()],
                    component_id=comp_id,
                    element_id=form_id,
                    edge_case_type=code,
                    assertions=["expect(formElement).toBeInTheDocument()", f"expect(formElement).toHaveTextContent('{expected[:20]}')"],
                    locator_rtl=rtl_loc,
                    locator_angular=ang_loc,
                    jest_matcher="toBeInTheDocument",
                    mock_requirements=[],
                    expected_state_changes={},
                    expected_dom_changes=["validation error visible"]
                )
            )

        return edge_cases


class EventEdgeCaseGenerator(BaseEdgeCaseGenerator):
    """Generates edge cases for Event Handling and User Interaction categories."""

    @property
    def category_name(self) -> str:
        return "Events"

    def supports(self, strategy: TestStrategy) -> bool:
        return strategy.category in ("Event Handling Tests", "User Interaction Tests") or "EVT" in strategy.id

    def generate(self, strategy: TestStrategy) -> List[EdgeCaseScenario]:
        strat_id = strategy.id
        target = strategy.target_component
        comp_id = strategy.component_id or f"comp_{target}"
        event_id = strategy.event_id
        element_id = strategy.element_id
        edge_cases = []

        priority = get_dynamic_priority(target, "Medium")
        ir = get_cached_ir()
        event_meta = None
        if ir and event_id:
            event_meta = next((ev for ev in ir.events if ev.id == event_id), None)

        # Standard interaction edge cases
        scenarios = [
            ("SINGLE-CLICK", "Single Click", "Trigger standard single click action", "Event handler fires once and resolves successfully."),
            ("RAPID-CLICK", "Rapid Click", "Simulate multiple rapid consecutive clicks", "Debounce or throttle prevents duplicate actions or duplicate API calls."),
            ("DISABLED-INTERACTION", "Disabled Interaction", "Trigger click action on disabled element", "No callback function should run."),
        ]

        # preventDefault
        if event_meta and event_meta.prevent_default:
            scenarios.append(("PREVENT-DEFAULT", "preventDefault", "Verify event default behavior is prevented", "Calls e.preventDefault() correctly."))

        # stopPropagation
        if event_meta and event_meta.stop_propagation:
            scenarios.append(("STOP-PROPAGATION", "stopPropagation", "Verify click event propagation is stopped", "Calls e.stopPropagation() correctly."))

        # Keyboard Enter / Space
        if event_meta and any(x in event_meta.event_type.lower() for x in ["key", "enter", "escape", "tab"]):
            scenarios.append(("KEYBOARD-ENTER", "Keyboard Enter", "Trigger handler using Enter key", "Executes event handler exactly like physical pointer click."))
            scenarios.append(("KEYBOARD-SPACE", "Keyboard Space", "Trigger handler using Spacebar", "Executes event handler cleanly."))

        # Tab Navigation focus/blur
        if event_meta and any(x in event_meta.event_type.lower() for x in ["focus", "blur"]):
            scenarios.append(("FOCUS-BLUR", "Focus/Blur", "Simulate focus entry and focus blur escape", "Verify focus outline classes adjust correctly."))

        for code, case_type, desc, expected in scenarios:
            ec_id = f"EC-{strat_id}-{code}"
            
            rtl_loc = f"screen.getByRole('button')"
            ang_loc = f"by.css('button')"
            if ir and element_id:
                el = next((e for e in ir.elements if e.id == element_id), None)
                if el:
                    rtl_loc = el.locator_rtl or rtl_loc
                    ang_loc = el.locator_angular or ang_loc

            edge_cases.append(
                EdgeCaseScenario(
                    id=ec_id,
                    strategy_id=strat_id,
                    category=self.category_name,
                    priority=priority,
                    title=f"Event: {case_type}",
                    description=f"Validate event/user interaction '{desc.lower()}' on {target}.",
                    input_data={"event_id": event_id},
                    expected_behavior=expected,
                    tags=["events", "interaction", code.lower()],
                    component_id=comp_id,
                    event_id=event_id,
                    element_id=element_id,
                    edge_case_type=code,
                    assertions=["expect(handlerSpy).toHaveBeenCalled()"],
                    locator_rtl=rtl_loc,
                    locator_angular=ang_loc,
                    jest_matcher="toHaveBeenCalled",
                    mock_requirements=["jest.fn() handler spy"],
                    expected_state_changes={},
                    expected_dom_changes=["callback side effect complete"]
                )
            )

        return edge_cases


class StateEdgeCaseGenerator(BaseEdgeCaseGenerator):
    """Generates edge cases for State Management and Component Initialization categories."""

    @property
    def category_name(self) -> str:
        return "State"

    def supports(self, strategy: TestStrategy) -> bool:
        ir = get_cached_ir()
        comp_name = strategy.target_component
        
        # Check if state variables exist for this component in IR
        if ir:
            comp = next((c for c in ir.components if c.name == comp_name), None)
            # Find if this component has state variables
            has_state = any(s.component_name == comp_name for s in ir.state)
            if not has_state:
                return False
                
        return strategy.category in ("State Management Tests", "Component Initialization", "State") or "STATE" in strategy.id

    def generate(self, strategy: TestStrategy) -> List[EdgeCaseScenario]:
        strat_id = strategy.id
        target = strategy.target_component
        comp_id = strategy.component_id or f"comp_{target}"
        state_id = strategy.state_id
        edge_cases = []

        priority = get_dynamic_priority(target, "Medium")
        ir = get_cached_ir()
        state_meta = None
        if ir and state_id:
            state_meta = next((s for s in ir.state if s.id == state_id), None)

        scenarios = [
            ("INITIAL-STATE", "Initial State", "Verify initial state bindings", "State resolves to default initialization values on mount."),
        ]

        if state_meta:
            scenarios.append(("STATE-TRANSITION", "State Transition", f"Trigger state setter on '{state_meta.name}'", f"State transition updates to new value successfully."))
            
            if state_meta.state_type == "boolean":
                scenarios.append(("TOGGLE-STATE", "Toggle State", f"Toggle boolean state '{state_meta.name}' true/false", "Toggles state values back and forth."))

        # Check if multiple updates, async updates, reset exist
        if ir:
            has_api = any(svc.component_name == target for svc in ir.services)
            if has_api:
                scenarios.append(("ASYNC-UPDATES", "Async Updates", "Trigger state updates post asynchronous API promises", "UI displays loading indicator, then resolves state update."))
            
            has_reset = any(ev.event_type == "reset" for ev in ir.events if ev.component_name == target)
            if has_reset:
                scenarios.append(("RESET-STATE", "Reset State", "Trigger reset handler to clear state", "State variables reset back to initial values."))

        for code, case_type, desc, expected in scenarios:
            ec_id = f"EC-{strat_id}-{code}"

            edge_cases.append(
                EdgeCaseScenario(
                    id=ec_id,
                    strategy_id=strat_id,
                    category=self.category_name,
                    priority=priority,
                    title=f"State: {case_type}",
                    description=f"Validate component state transitions: {desc.lower()}.",
                    input_data={"state_id": state_id},
                    expected_behavior=expected,
                    tags=["state", "lifecycle", code.lower()],
                    component_id=comp_id,
                    state_id=state_id,
                    edge_case_type=code,
                    assertions=["expect(element).toHaveTextContent(newValue)"],
                    locator_rtl="screen.getByRole('generic')",
                    locator_angular="by.css('div')",
                    jest_matcher="toHaveTextContent",
                    mock_requirements=[],
                    expected_state_changes={state_meta.name if state_meta else "state": "newValue"},
                    expected_dom_changes=["text value changed in DOM"]
                )
            )

        return edge_cases


class ServiceEdgeCaseGenerator(BaseEdgeCaseGenerator):
    """Generates edge cases for API/Service Interaction and Error Handling categories."""

    @property
    def category_name(self) -> str:
        return "Services"

    def supports(self, strategy: TestStrategy) -> bool:
        ir = get_cached_ir()
        comp_name = strategy.target_component
        
        # Check if services exist in IR
        if ir:
            has_service = any(svc.component_name == comp_name or svc.name == comp_name for svc in ir.services)
            if not has_service:
                return False
                
        return strategy.category in ("API/Service Interaction Tests", "Error Handling Tests", "Services") or "SVC" in strategy.id

    def generate(self, strategy: TestStrategy) -> List[EdgeCaseScenario]:
        strat_id = strategy.id
        target = strategy.target_component
        comp_id = strategy.component_id or f"comp_{target}"
        service_id = strategy.service_id
        edge_cases = []

        priority = get_dynamic_priority(target, "High")
        ir = get_cached_ir()
        service_meta = None
        if ir and service_id:
            service_meta = next((s for s in ir.services if s.id == service_id), None)

        scenarios = [
            ("SUCCESS", "Success", "Mock successful service resolution", "Update components' state and render payload data correctly."),
            ("FAILURE-500", "API Failure (500)", "Mock server HTTP 500 error response", "Render user-friendly error banners and prevent application crash."),
            ("TIMEOUT", "Timeout", "Simulate network request latency/timeout", "Retry request or render latency warnings in UI."),
            ("EMPTY-RESPONSE", "Empty Response", "Mock empty payload (e.g. empty list/object)", "Show list empty state placeholders."),
            ("INVALID-RESPONSE", "Invalid Response", "Mock malformed or bad JSON payloads", "Handle JSON parsing errors gracefully and avoid blank screens."),
            ("NETWORK-FAILURE", "Network failure", "Mock offline network error connection", "Render network offline warning indicators.")
        ]

        for code, case_type, desc, expected in scenarios:
            ec_id = f"EC-{strat_id}-{code}"

            edge_cases.append(
                EdgeCaseScenario(
                    id=ec_id,
                    strategy_id=strat_id,
                    category=self.category_name,
                    priority=priority,
                    title=f"Service: {case_type}",
                    description=f"Validate that '{target}' handles service API case: {desc.lower()}.",
                    input_data={"service_id": service_id},
                    expected_behavior=expected,
                    tags=["services", "api", "mock", code.lower()],
                    component_id=comp_id,
                    service_id=service_id,
                    edge_case_type=code,
                    assertions=["expect(serviceMock).toHaveBeenCalled()"],
                    locator_rtl="screen.getByRole('alert')" if "fail" in code.lower() else "screen.getByRole('generic')",
                    locator_angular="by.css('.alert')" if "fail" in code.lower() else "by.css('div')",
                    jest_matcher="toHaveBeenCalled",
                    mock_requirements=[f"mockResolvedValue() for success" if "success" in code.lower() else "mockRejectedValue() for error"],
                    expected_state_changes={},
                    expected_dom_changes=["UI updates based on service state"]
                )
            )

        return edge_cases


class RouteEdgeCaseGenerator(BaseEdgeCaseGenerator):
    """Generates edge cases for Routing categories."""

    @property
    def category_name(self) -> str:
        return "Routing"

    def supports(self, strategy: TestStrategy) -> bool:
        ir = get_cached_ir()
        comp_name = strategy.target_component
        
        # Check if routes exist in IR
        if ir:
            if not ir.routes:
                return False
                
        return strategy.category in ("Routing Tests", "Routing") or "ROUTE" in strategy.id

    def generate(self, strategy: TestStrategy) -> List[EdgeCaseScenario]:
        strat_id = strategy.id
        target = strategy.target_component
        comp_id = strategy.component_id or f"comp_{target}"
        route_id = strategy.route_id
        edge_cases = []

        priority = get_dynamic_priority(target, "Medium")
        ir = get_cached_ir()
        route_meta = None
        if ir and route_id:
            route_meta = next((r for r in ir.routes if r.id == route_id), None)

        scenarios = [
            ("INVALID-ROUTE", "Invalid route", "Navigate to unregistered URL path", "Redirect to 404 fallback page or root path."),
            ("BACK-FORWARD", "Browser Back/Forward", "Perform browser history popstate actions", "Sync view component state with browser location path."),
            ("REFRESH", "Refresh", "Trigger page refresh on route", "Retain route parameters or reload fresh state data."),
        ]

        if route_meta:
            if ":" in route_meta.path:
                scenarios.append(("MISSING-PARAMETER", "Missing parameter", "Route with missing path parameters", "Redirect or fail gracefully."))
                scenarios.append(("INVALID-PARAMETER", "Invalid parameter", "Route with malformed or invalid path parameters", "Handle parameter error UI fallback."))
            if route_meta.guard:
                scenarios.append(("UNAUTHORIZED-ROUTE", "Unauthorized Route", "Access protected path unauthenticated", "Route guard intercepts and redirects to login path."))

        for code, case_type, desc, expected in scenarios:
            ec_id = f"EC-{strat_id}-{code}"

            edge_cases.append(
                EdgeCaseScenario(
                    id=ec_id,
                    strategy_id=strat_id,
                    category=self.category_name,
                    priority=priority,
                    title=f"Routing: {case_type}",
                    description=f"Validate router behavior for: {desc.lower()}.",
                    input_data={"route_id": route_id},
                    expected_behavior=expected,
                    tags=["routing", "navigation", code.lower()],
                    component_id=comp_id,
                    route_id=route_id,
                    edge_case_type=code,
                    assertions=["expect(location.path()).toBe(targetPath)"],
                    locator_rtl="container.querySelector('router-outlet')",
                    locator_angular="by.css('router-outlet')",
                    jest_matcher="toBe",
                    mock_requirements=["mock Router and Location"],
                    expected_state_changes={},
                    expected_dom_changes=["route component rendered"]
                )
            )

        return edge_cases


class AccessibilityEdgeCaseGenerator(BaseEdgeCaseGenerator):
    """Generates edge cases for Accessibility (a11y) categories."""

    @property
    def category_name(self) -> str:
        return "Accessibility"

    def supports(self, strategy: TestStrategy) -> bool:
        ir = get_cached_ir()
        comp_name = strategy.target_component
        
        # Check if accessibility exists in IR
        if ir:
            comp = next((c for c in ir.components if c.name == comp_name), None)
            if comp and not comp.accessibility:
                return False
                
        return strategy.category in ("Accessibility Tests", "Accessibility") or "A11Y" in strategy.id

    def generate(self, strategy: TestStrategy) -> List[EdgeCaseScenario]:
        strat_id = strategy.id
        target = strategy.target_component
        comp_id = strategy.component_id or f"comp_{target}"
        edge_cases = []

        priority = get_dynamic_priority(target, "Low")
        ir = get_cached_ir()
        comp_meta = None
        if ir:
            comp_meta = next((c for c in ir.components if c.name == target), None)

        acc = comp_meta.accessibility if comp_meta else None

        scenarios = [
            ("KEYBOARD-NAV", "Keyboard navigation", "Navigate active inputs/buttons via Tab/Shift+Tab keys", "Cycle focuses sequentially; verify no focus traps occur."),
            ("FOCUS-ORDER", "Focus order", "Verify keyboard focus path matches semantic DOM order", "Interactive elements maintain expected tab index outline flow."),
        ]

        if acc:
            if acc.alt_texts:
                scenarios.append(("EMPTY-ALT", "Empty alt", "Render image tags with missing or empty alt values", "Ensure image has descriptive alternative text or role='presentation'."))
            if acc.roles or acc.aria_attributes:
                scenarios.append(("ARIA-ROLES", "Role validation", "Check roles mapping on custom element layouts", "Required ARIA roles and labels are structurally correct."))

        for code, case_type, desc, expected in scenarios:
            ec_id = f"EC-{strat_id}-{code}"

            edge_cases.append(
                EdgeCaseScenario(
                    id=ec_id,
                    strategy_id=strat_id,
                    category=self.category_name,
                    priority=priority,
                    title=f"A11y: {case_type}",
                    description=f"Validate accessibility edge case: {desc.lower()}.",
                    input_data={},
                    expected_behavior=expected,
                    tags=["accessibility", "a11y", "aria", code.lower()],
                    component_id=comp_id,
                    edge_case_type=code,
                    assertions=["expect(element).toHaveAttribute('role')"],
                    locator_rtl="screen.getByRole('generic')",
                    locator_angular="by.css('div')",
                    jest_matcher="toHaveAttribute",
                    mock_requirements=[],
                    expected_state_changes={},
                    expected_dom_changes=["attributes verified in DOM"]
                )
            )

        return edge_cases


class PropEdgeCaseGenerator(BaseEdgeCaseGenerator):
    """Generates edge cases for Props rendering categories."""

    @property
    def category_name(self) -> str:
        return "State"  # Map to existing Pydantic categories: Forms, Events, State, Services, Routing, Accessibility

    def supports(self, strategy: TestStrategy) -> bool:
        return "REND-PROPS" in strategy.id or "PROPS" in strategy.id or strategy.category == "Rendering Tests"

    def generate(self, strategy: TestStrategy) -> List[EdgeCaseScenario]:
        strat_id = strategy.id
        target = strategy.target_component
        comp_id = strategy.component_id or f"comp_{target}"
        edge_cases = []

        priority = get_dynamic_priority(target, "Medium")
        ir = get_cached_ir()
        comp_meta = None
        if ir:
            comp_meta = next((c for c in ir.components if c.name == target), None)

        props = comp_meta.props_inputs if comp_meta else []
        if not props:
            return []

        # Generate edge cases for the first prop to avoid explosion, or for all props if few
        for prop in props[:3]:  # Cap at first 3 props to prevent strategy plan blowup
            prop_name = prop.get("name", "prop")
            
            scenarios = [
                (f"PROP-{prop_name}-NULL", "null", f"Pass null for prop '{prop_name}'", "Component handles null gracefully without crashing."),
                (f"PROP-{prop_name}-UNDEFINED", "undefined", f"Pass undefined for prop '{prop_name}'", "Component uses default prop fallback value."),
                (f"PROP-{prop_name}-EMPTY", "empty string", f"Pass empty string for prop '{prop_name}'", "Component handles empty values successfully."),
                (f"PROP-{prop_name}-SPECIAL", "special characters", f"Pass special characters & emojis for prop '{prop_name}'", "Component renders unicode special characters safely.")
            ]

            for code, case_type, desc, expected in scenarios:
                ec_id = f"EC-{strat_id}-{code}"

                edge_cases.append(
                    EdgeCaseScenario(
                        id=ec_id,
                        strategy_id=strat_id,
                        category=self.category_name,
                        priority=priority,
                        title=f"Prop: {prop_name} ({case_type})",
                        description=f"Validate component handling of prop '{prop_name}' under edge case: {desc.lower()}.",
                        input_data={prop_name: None if "null" in case_type else "undefined"},
                        expected_behavior=expected,
                        tags=["props", "validation", code.lower()],
                        component_id=comp_id,
                        edge_case_type=code,
                        assertions=["expect(element).toBeInTheDocument()"],
                        locator_rtl="screen.getByRole('generic')",
                        locator_angular="by.css('div')",
                        jest_matcher="toBeInTheDocument",
                        mock_requirements=[],
                        expected_state_changes={},
                        expected_dom_changes=["rendered correctly"]
                    )
                )

        return edge_cases


class RenderingEdgeCaseGenerator(BaseEdgeCaseGenerator):
    """Generates edge cases for Component Initialization and Rendering categories."""

    @property
    def category_name(self) -> str:
        return "State"

    def supports(self, strategy: TestStrategy) -> bool:
        return (
            "REND-INIT" in strategy.id
            or "INIT" in strategy.id
            or strategy.category in ("Component Initialization", "Rendering Tests", "Conditional Rendering Tests")
        )

    def generate(self, strategy: TestStrategy) -> List[EdgeCaseScenario]:
        strat_id = strategy.id
        target = strategy.target_component
        comp_id = strategy.component_id or f"comp_{target}"
        priority = get_dynamic_priority(target, "Medium")

        ec_id = f"EC-{strat_id}-MOUNT-STABILITY"
        return [
            EdgeCaseScenario(
                id=ec_id,
                strategy_id=strat_id,
                category=self.category_name,
                priority=priority,
                title=f"Mount: {target} Initial Render",
                description=f"Validate initial mount layout stability and DOM rendering of component '{target}'.",
                input_data={"render_context": "initial_mount"},
                expected_behavior=f"{target} component renders its root layout node without runtime exceptions.",
                tags=["mount", "lifecycle", "initial_render"],
                component_id=comp_id,
                edge_case_type="MOUNT",
                assertions=["expect(element).toBeInTheDocument()"],
                locator_rtl="container.querySelector('div')",
                locator_angular="by.css('div')",
                jest_matcher="toBeInTheDocument",
                mock_requirements=[],
                expected_state_changes={},
                expected_dom_changes=["component mounted in DOM"]
            )
        ]
