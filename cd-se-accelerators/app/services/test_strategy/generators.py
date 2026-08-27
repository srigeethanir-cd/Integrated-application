"""
Concrete Strategy Generators – Module 5.

Implements framework-agnostic base test strategy generators:
- ComponentStrategyGenerator (Mounting, rendering, and conditional layouts)
- FormStrategyGenerator (Inputs, validators, and submit paths)
- StateStrategyGenerator (Reactive states, transition logs)
- ServiceStrategyGenerator (API calls, errors, pending spinners)
- RouteStrategyGenerator (Routing, paths, guards)
- AccessibilityStrategyGenerator (WCAG, ARIA roles, key navigation)
- EventStrategyGenerator (User pointer / key events)
- ContextStrategyGenerator (Redux / Context consumption)
- HookStrategyGenerator (Hooks lifecycle side-effects)
"""

import logging
from typing import List, Optional
from app.models.ir_models import FrameworkAgnosticIR, ComponentIR
from app.models.strategy_models import TestStrategy
from app.services.test_strategy.base_generator import BaseStrategyGenerator

logger = logging.getLogger(__name__)


def get_priority_by_risk(ir: FrameworkAgnosticIR, comp_name: str) -> str:
    """Helper to dynamically calculate priority level from ComponentIR risk_score."""
    comp = next((c for c in ir.components if c.name == comp_name), None)
    if comp and comp.risk_score is not None:
        score = comp.risk_score
        if score >= 7.0:
            return "High"
        elif score >= 4.0:
            return "Medium"
        else:
            return "Low"
    return "Medium"


def get_risk_str(ir: FrameworkAgnosticIR, comp_name: str) -> str:
    """Helper to format risk description string."""
    comp = next((c for c in ir.components if c.name == comp_name), None)
    if comp:
        score = comp.risk_score or 1.0
        level = "High" if score >= 7.0 else "Medium" if score >= 4.0 else "Low"
        return f"{level} ({int(score)}/10)"
    return "Medium (5/10)"


def get_risk_reason(ir: FrameworkAgnosticIR, comp_name: str) -> str:
    """Helper to extract risk justification reason."""
    comp = next((c for c in ir.components if c.name == comp_name), None)
    if comp and comp.risk_analysis:
        return "; ".join(comp.risk_analysis.risk_reasons) or comp.behavior_summary or "Component behavior profile."
    return "Standard component validation."


class ComponentStrategyGenerator(BaseStrategyGenerator):
    """Generates Component Initialization, Rendering, and Conditional Rendering strategies."""

    @property
    def category_name(self) -> str:
        return "Rendering Tests"

    def generate(self, ir: FrameworkAgnosticIR) -> List[TestStrategy]:
        strategies: List[TestStrategy] = []
        for comp in ir.components:
            comp_name = comp.name
            comp_id = comp.id or f"comp_{comp_name}"
            priority = get_priority_by_risk(ir, comp_name)
            risk_str = get_risk_str(ir, comp_name)
            reason_str = get_risk_reason(ir, comp_name)

            # 1. Initial Render Strategy (Component Initialization)
            strat_id = f"STRAT-{comp_name}-REND-INIT"
            strategies.append(
                TestStrategy(
                    id=strat_id,
                    category="Component Initialization",
                    priority=priority,
                    target_component=comp_name,
                    description=f"Verify {comp_name} performs an initial render and mounts cleanly in the DOM tree.",
                    preconditions=["DOM simulation environment is loaded"],
                    coverage_tags=["mount", "lifecycle", "initial_render"],
                    strategy_id=strat_id,
                    component_id=comp_id,
                    risk=risk_str,
                    reason=reason_str,
                    behavior_reference=comp.behavior_summary or f"Initial layout of {comp_name}",
                    test_objective=f"Assert {comp_name} mounts cleanly on startup.",
                    expected_outcome=f"{comp_name} component renders its root layout node without runtime exceptions."
                )
            )

            # 2. Props Rendering Strategy
            if comp.props_inputs:
                prop_names = [p.get("name", "prop") for p in comp.props_inputs if p.get("name")]
                strat_id = f"STRAT-{comp_name}-REND-PROPS"
                strategies.append(
                    TestStrategy(
                        id=strat_id,
                        category="Rendering Tests",
                        priority=priority,
                        target_component=comp_name,
                        description=f"Verify component {comp_name} correctly processes and displays incoming props: {', '.join(prop_names)}.",
                        preconditions=[f"Configure valid test input values for props: {', '.join(prop_names)}"],
                        coverage_tags=["render", "props"],
                        strategy_id=strat_id,
                        component_id=comp_id,
                        risk=risk_str,
                        reason=reason_str,
                        behavior_reference=f"Props model for {comp_name}",
                        test_objective=f"Validate correct binding and presentation of prop attributes: {prop_names}.",
                        expected_outcome=f"Incoming prop values are rendered correctly within their target layout elements."
                    )
                )

            # 3. Child Component Rendering (Integration)
            if comp.children_ids:
                strat_id = f"STRAT-{comp_name}-REND-CHILDREN"
                child_names = ", ".join(comp.children)
                strategies.append(
                    TestStrategy(
                        id=strat_id,
                        category="Rendering Tests",
                        priority=priority,
                        target_component=comp_name,
                        description=f"Verify {comp_name} integrates and renders its children components: {child_names}.",
                        preconditions=["DOM container is mounted"],
                        coverage_tags=["render", "children", "integration"],
                        strategy_id=strat_id,
                        component_id=comp_id,
                        risk=risk_str,
                        reason=reason_str,
                        behavior_reference=f"Parent-child linkage: parent={comp_name}, children={child_names}",
                        test_objective=f"Validate layout embedding for children: {child_names}.",
                        expected_outcome=f"All child component selectors render their layout templates inside the parent layout."
                    )
                )

            # 4. Conditional Rendering Strategy
            for cr in comp.render_conditions:
                cond_expr = cr.condition
                strat_id = f"STRAT-{comp_name}-REND-COND-{cond_expr}"
                strategies.append(
                    TestStrategy(
                        id=strat_id,
                        category="Conditional Rendering Tests",
                        priority=priority,
                        target_component=comp_name,
                        description=f"Verify conditional visibility of elements ({', '.join(cr.affected_ui)}) when condition '{cond_expr}' is updated.",
                        preconditions=[f"Toggle reactive state variables driving condition: {', '.join(cr.dependent_state)}"],
                        coverage_tags=["conditional", "visibility", cond_expr],
                        strategy_id=strat_id,
                        component_id=comp_id,
                        risk=risk_str,
                        reason=reason_str,
                        behavior_reference=f"RenderCondition: '{cond_expr}' -> '{cr.visibility_rule}'",
                        test_objective=f"Verify visual toggle branch for condition '{cond_expr}'.",
                        expected_outcome=f"Elements toggle visibility dynamically according to: '{cr.visibility_rule}'."
                    )
                )

            # 5. Empty State Strategy
            comp_elements = [el for el in ir.elements if el.component_name == comp_name]
            has_list = any(el.tag in ["ul", "ol", "table", "tbody"] for el in comp_elements)
            if has_list:
                strat_id = f"STRAT-{comp_name}-REND-EMPTY"
                strategies.append(
                    TestStrategy(
                        id=strat_id,
                        category="Rendering Tests",
                        priority=priority,
                        target_component=comp_name,
                        description=f"Verify {comp_name} handles empty data collections gracefully by showing a placeholder layout.",
                        preconditions=["Pass empty dataset array as prop or state"],
                        coverage_tags=["render", "empty_state", "boundary"],
                        strategy_id=strat_id,
                        component_id=comp_id,
                        risk=risk_str,
                        reason=reason_str,
                        behavior_reference=f"Empty state handling on list collection",
                        test_objective=f"Verify boundary case when dataset collection has length = 0.",
                        expected_outcome="Graceful placeholder layout or 'No results' banner is rendered; no console errors."
                    )
                )

        return strategies


class StateStrategyGenerator(BaseStrategyGenerator):
    """Generates State Management strategies."""

    @property
    def category_name(self) -> str:
        return "State Management Tests"

    def generate(self, ir: FrameworkAgnosticIR) -> List[TestStrategy]:
        strategies: List[TestStrategy] = []
        for comp in ir.components:
            comp_name = comp.name
            comp_id = comp.id or f"comp_{comp_name}"
            priority = get_priority_by_risk(ir, comp_name)
            risk_str = get_risk_str(ir, comp_name)
            reason_str = get_risk_reason(ir, comp_name)

            # 1. State Initialization
            if comp.state_transitions:
                st_names = [st.current_state.split(" = ")[0] for st in comp.state_transitions]
                strat_id = f"STRAT-{comp_name}-STATE-INIT"
                strategies.append(
                    TestStrategy(
                        id=strat_id,
                        category="State Management Tests",
                        priority=priority,
                        target_component=comp_name,
                        description=f"Verify reactive state variables ({', '.join(st_names)}) initialize to their default values on mount.",
                        preconditions=["Component is rendered"],
                        coverage_tags=["state", "initial_value"],
                        strategy_id=strat_id,
                        component_id=comp_id,
                        risk=risk_str,
                        reason=reason_str,
                        behavior_reference=f"State variables: {', '.join(st_names)}",
                        test_objective=f"Assert default initial states are correctly mapped.",
                        expected_outcome="All state properties register their default initial values."
                    )
                )

            # 2. State Transitions
            for st in comp.state_transitions:
                st_var = st.current_state.split(" = ")[0]
                strat_id = f"STRAT-{comp_name}-STATE-TRANS-{st_var}"
                strategies.append(
                    TestStrategy(
                        id=strat_id,
                        category="State Management Tests",
                        priority=priority,
                        target_component=comp_name,
                        description=f"Verify state variable '{st_var}' transitions correctly from '{st.current_state}' to '{st.next_state}' on trigger '{st.trigger}'.",
                        preconditions=[f"Component is in state '{st.current_state}'"],
                        coverage_tags=["state", "transition", st_var],
                        strategy_id=strat_id,
                        component_id=comp_id,
                        state_id=f"state_{comp_id}_{st_var}",
                        risk=risk_str,
                        reason=reason_str,
                        behavior_reference=f"Transition: {st.current_state} -> {st.trigger} -> {st.next_state}",
                        test_objective=f"Assert correct transition lifecycle for state '{st_var}'.",
                        expected_outcome=f"State updates to '{st.next_state}' and triggers rendering updates on elements: {', '.join(st.affected_elements)}."
                    )
                )

        return strategies


class EventStrategyGenerator(BaseStrategyGenerator):
    """Generates Event Handling and User Interaction strategies."""

    @property
    def category_name(self) -> str:
        return "Event Handling Tests"

    def generate(self, ir: FrameworkAgnosticIR) -> List[TestStrategy]:
        strategies: List[TestStrategy] = []
        for comp in ir.components:
            comp_name = comp.name
            comp_id = comp.id or f"comp_{comp_name}"
            priority = get_priority_by_risk(ir, comp_name)
            risk_str = get_risk_str(ir, comp_name)
            reason_str = get_risk_reason(ir, comp_name)

            for ig in comp.interaction_graph:
                handler = ig.handler
                event_type = ig.event
                strat_id = f"STRAT-{comp_name}-EVT-{handler}"
                
                # Link target element ID if found
                target_el_id = None
                for ev in ir.events:
                    if ev.component_name == comp_name and ev.handler_name == handler:
                        target_el_id = ev.target_element_id
                        break

                strategies.append(
                    TestStrategy(
                        id=strat_id,
                        category="Event Handling Tests",
                        priority=priority,
                        target_component=comp_name,
                        target_function=f"{handler}()",
                        description=f"Verify event handler '{handler}' triggers correctly on user action '{ig.user_action}' and executes side-effects.",
                        preconditions=[f"Interactive element with event handler '{handler}' is render-ready"],
                        coverage_tags=["event", event_type, handler],
                        strategy_id=strat_id,
                        component_id=comp_id,
                        element_id=target_el_id,
                        event_id=f"evt_{comp_id}_{handler}",
                        risk=risk_str,
                        reason=reason_str,
                        behavior_reference=f"Interaction: {ig.user_action} -> invoke {handler}",
                        test_objective=f"Verify user interaction triggers callback '{handler}' and performs updates.",
                        expected_outcome=f"Callback executes cleanly, performing updates: '{ig.business_effect}' and DOM updates: '{ig.dom_change}'."
                    )
                )

            # Modifiers preventDefault / stopPropagation
            for ev in ir.events:
                if ev.component_name == comp_name and (ev.prevent_default or ev.stop_propagation):
                    handler = ev.handler_name
                    strat_id = f"STRAT-{comp_name}-EVT-MOD-{handler}"
                    strategies.append(
                        TestStrategy(
                            id=strat_id,
                            category="Event Handling Tests",
                            priority=priority,
                            target_component=comp_name,
                            target_function=f"{handler}()",
                            description=f"Verify event modifiers (preventDefault: {ev.prevent_default}, stopPropagation: {ev.stop_propagation}) are applied in event handler '{handler}'.",
                            preconditions=["Render component within bubbling test tree"],
                            coverage_tags=["event", "modifier", handler],
                            strategy_id=strat_id,
                            component_id=comp_id,
                            event_id=ev.id,
                            element_id=ev.target_element_id,
                            risk=risk_str,
                            reason=reason_str,
                            behavior_reference=f"Event modifiers for handler {handler}",
                            test_objective=f"Assert default browser behaviors and event propagation are suppressed in {handler}.",
                            expected_outcome=f"Event is intercepted; default action is prevented, bubble propagation is halted."
                        )
                    )

        return strategies


class FormStrategyGenerator(BaseStrategyGenerator):
    """Generates Form Validation strategies."""

    @property
    def category_name(self) -> str:
        return "Form Validation Tests"

    def generate(self, ir: FrameworkAgnosticIR) -> List[TestStrategy]:
        strategies: List[TestStrategy] = []
        for form in ir.forms:
            form_name = form.name
            comp_name = form.component_name
            comp_id = get_unique_comp_id_from_name(ir, comp_name)
            form_id = form.id or f"form_{comp_name}_{form_name}"
            priority = get_priority_by_risk(ir, comp_name)
            risk_str = get_risk_str(ir, comp_name)
            reason_str = get_risk_reason(ir, comp_name)
            
            control_names = [c.name for c in form.controls]

            # 1. Success Path (Positive Case)
            sub_handler = form.submit_handler or "handleSubmit"
            if not sub_handler.endswith("()"):
                sub_handler = f"{sub_handler}()"

            strat_id = f"STRAT-{comp_name}-{form_name}-FORM-SUCCESS"
            strategies.append(
                TestStrategy(
                    id=strat_id,
                    category="Form Validation Tests",
                    priority=priority,
                    target_component=comp_name,
                    target_function=sub_handler,
                    description=f"Verify successful form submission using valid control values ({', '.join(control_names)}) invokes onSubmit handler '{sub_handler}'.",
                    preconditions=["Submit form with valid fields data"],
                    coverage_tags=["form", "submit", "success"],
                    strategy_id=strat_id,
                    component_id=comp_id,
                    element_id=form_id,
                    risk=risk_str,
                    reason=reason_str,
                    behavior_reference=f"Form Model: library={form.library}, submit_handler={form.submit_handler}",
                    test_objective=f"Assert positive submit path triggers handler with clean payload.",
                    expected_outcome=f"Form payload validation checks pass and event submit handler triggers successfully."
                )
            )

            # 2. Validation Constraints (Negative Case)
            if any(c.is_required or c.validation_rules for c in form.controls):
                strat_id = f"STRAT-{comp_name}-{form_name}-FORM-VALIDATION"
                strategies.append(
                    TestStrategy(
                        id=strat_id,
                        category="Form Validation Tests",
                        priority=priority,
                        target_component=comp_name,
                        target_function=sub_handler,
                        description=f"Verify input fields trigger validation rules and prevent submission when invalid data is supplied.",
                        preconditions=["Submit form with empty required fields or malformed formatting"],
                        coverage_tags=["form", "validation", "error"],
                        strategy_id=strat_id,
                        component_id=comp_id,
                        element_id=form_id,
                        risk=risk_str,
                        reason=reason_str,
                        behavior_reference=f"Form control validators: {control_names}",
                        test_objective=f"Verify validation locks submit action and renders error feedback text.",
                        expected_outcome="Submit action is blocked; input fields display visual error styles or warning texts."
                    )
                )

        return strategies


class ServiceStrategyGenerator(BaseStrategyGenerator):
    """Generates API/Service Interaction, Error Handling, and Async behavior strategies."""

    @property
    def category_name(self) -> str:
        return "API/Service Interaction Tests"

    def generate(self, ir: FrameworkAgnosticIR) -> List[TestStrategy]:
        strategies: List[TestStrategy] = []
        for svc in ir.services:
            svc_name = svc.name
            comp_name = svc.component_name or "global"
            comp_id = get_unique_comp_id_from_name(ir, comp_name) if svc.component_name else None
            svc_id = svc.id or f"svc_{svc_name}"
            priority = get_priority_by_risk(ir, comp_name) if svc.component_name else "Medium"
            risk_str = get_risk_str(ir, comp_name) if svc.component_name else "Medium (5/10)"
            reason_str = get_risk_reason(ir, comp_name) if svc.component_name else "External dependency validation."

            # Inspect API call details if present
            api_info = svc.api_calls[0] if svc.api_calls else {}
            endpoint = api_info.get("endpoint") or "API call"
            method = api_info.get("http_method") or "HTTP request"
            fn_name = f"{svc_name}()" if not svc_name.endswith("()") else svc_name

            # 1. API Call Success (Positive Case)
            strat_id = f"STRAT-{comp_name}-API-SUCCESS-{svc_name}"
            strategies.append(
                TestStrategy(
                    id=strat_id,
                    category="API/Service Interaction Tests",
                    priority=priority,
                    target_component=comp_name,
                    target_function=fn_name,
                    description=f"Verify component successfully integrates API call '{svc_name}' ({method} {endpoint}) and updates state.",
                    preconditions=[f"Mock successful network payload for '{svc_name}'"],
                    coverage_tags=["api", "service", "success", svc_name],
                    strategy_id=strat_id,
                    component_id=comp_id,
                    service_id=svc_id,
                    risk=risk_str,
                    reason=reason_str,
                    behavior_reference=f"API Call: {method} {endpoint}",
                    test_objective=f"Verify success response maps back to local component state.",
                    expected_outcome=f"Network payload resolves successfully, state loads data, and layout renders response attributes."
                )
            )

            # 2. API Call Failure (Negative Case / Error Handling)
            strat_id = f"STRAT-{comp_name}-API-FAILURE-{svc_name}"
            strategies.append(
                TestStrategy(
                    id=strat_id,
                    category="Error Handling Tests",
                    priority=priority,
                    target_component=comp_name,
                    target_function=fn_name,
                    description=f"Verify error boundary handles network failures (HTTP 500/404) for API call '{svc_name}' ({method} {endpoint}) gracefully.",
                    preconditions=[f"Mock network rejection (HTTP 500) for '{svc_name}'"],
                    coverage_tags=["api", "error_handling", "failure", svc_name],
                    strategy_id=strat_id,
                    component_id=comp_id,
                    service_id=svc_id,
                    risk=risk_str,
                    reason=reason_str,
                    behavior_reference=f"Error boundary path for API: {method} {endpoint}",
                    test_objective=f"Assert API failures trigger visual error/alert states.",
                    expected_outcome="Network promise rejects, exception is caught, and alert banner or fallback warning renders."
                )
            )

            # 3. API Loading State (Async Behavior)
            loading_var = api_info.get("loading_state_var") or "loading"
            strat_id = f"STRAT-{comp_name}-API-ASYNC-{svc_name}"
            strategies.append(
                TestStrategy(
                    id=strat_id,
                    category="API/Service Interaction Tests",
                    priority=priority,
                    target_component=comp_name,
                    target_function=fn_name,
                    description=f"Verify loading state flag '{loading_var}' is toggled during the API call '{svc_name}' request lifecycle.",
                    preconditions=[f"Mock unresolved network promise for '{svc_name}'"],
                    coverage_tags=["api", "loading", "async", svc_name],
                    strategy_id=strat_id,
                    component_id=comp_id,
                    service_id=svc_id,
                    risk=risk_str,
                    reason=reason_str,
                    behavior_reference=f"Pending status: {method} {endpoint}",
                    test_objective=f"Assert visual loading indicator remains visible during unresolved promise flow.",
                    expected_outcome=f"Loading spinner mounts on pending request state, and unmounts once the promise resolves."
                )
            )

        return strategies


class RouteStrategyGenerator(BaseStrategyGenerator):
    """Generates Routing and Navigation strategies."""

    @property
    def category_name(self) -> str:
        return "Routing Tests"

    def generate(self, ir: FrameworkAgnosticIR) -> List[TestStrategy]:
        strategies: List[TestStrategy] = []
        for route in ir.routes:
            path = route.path
            comp_name = route.component or "RouteComponent"
            comp_id = get_unique_comp_id_from_name(ir, comp_name)
            route_id = route.id or f"route_{path.replace('/', '_')}"
            priority = get_priority_by_risk(ir, comp_name)
            risk_str = get_risk_str(ir, comp_name)
            reason_str = get_risk_reason(ir, comp_name)

            # 1. Navigation
            strat_id = f"STRAT-ROUTE-NAV-{comp_name}"
            strategies.append(
                TestStrategy(
                    id=strat_id,
                    category="Routing Tests",
                    priority=priority,
                    target_component=comp_name,
                    description=f"Verify client router navigates to path '{path}' and mounts the component '{comp_name}'.",
                    preconditions=[f"Configure router paths and trigger navigation to '{path}'"],
                    coverage_tags=["router", "navigation", path],
                    strategy_id=strat_id,
                    component_id=comp_id,
                    route_id=route_id,
                    risk=risk_str,
                    reason=reason_str,
                    behavior_reference=f"Route path: '{path}' -> mounts '{comp_name}'",
                    test_objective=f"Assert path '{path}' activates target layout component.",
                    expected_outcome=f"URL location is updated to '{path}' and component '{comp_name}' is rendered in route outlet."
                )
            )

            # 2. Route Parameters
            if route.route_params:
                strat_id = f"STRAT-ROUTE-PARAMS-{comp_name}"
                strategies.append(
                    TestStrategy(
                        id=strat_id,
                        category="Routing Tests",
                        priority=priority,
                        target_component=comp_name,
                        description=f"Verify route extracts parameters ({', '.join(route.route_params)}) correctly from URL path.",
                        preconditions=[f"Simulate navigation to parameter-bound URL: '{path}'"],
                        coverage_tags=["router", "params"],
                        strategy_id=strat_id,
                        component_id=comp_id,
                        route_id=route_id,
                        risk=risk_str,
                        reason=reason_str,
                        behavior_reference=f"URL parameter parser: {route.route_params}",
                        test_objective=f"Assert parameter values ({route.route_params}) are processed on route load.",
                        expected_outcome=f"Router params are parsed correctly and rendered or passed to local component states."
                    )
                )

        return strategies


class AccessibilityStrategyGenerator(BaseStrategyGenerator):
    """Generates WCAG Accessibility (a11y) strategies."""

    @property
    def category_name(self) -> str:
        return "Accessibility Tests"

    def generate(self, ir: FrameworkAgnosticIR) -> List[TestStrategy]:
        strategies: List[TestStrategy] = []
        for comp in ir.components:
            comp_name = comp.name
            comp_id = comp.id or f"comp_{comp_name}"
            priority = get_priority_by_risk(ir, comp_name)
            risk_str = get_risk_str(ir, comp_name)
            reason_str = get_risk_reason(ir, comp_name)
            
            acc = comp.accessibility_detail
            if acc and (acc.aria_roles or acc.labels or acc.keyboard_navigation):
                # 1. WCAG Roles and Labels
                strat_id = f"STRAT-{comp_name}-A11Y-AUDIT"
                strategies.append(
                    TestStrategy(
                        id=strat_id,
                        category="Accessibility Tests",
                        priority=priority,
                        target_component=comp_name,
                        description=f"Verify WCAG compliance: validate roles ({', '.join(acc.aria_roles)}), aria-labels / label associations ({', '.join(acc.labels)}), and alt text properties.",
                        preconditions=["Render component in clean DOM layout"],
                        coverage_tags=["a11y", "accessibility", "wcag"],
                        strategy_id=strat_id,
                        component_id=comp_id,
                        risk=risk_str,
                        reason=reason_str,
                        behavior_reference=f"Accessibility profiles: roles={acc.aria_roles}, labels={acc.labels}",
                        test_objective="Assert screen-reader friendly attributes are correctly set.",
                        expected_outcome="Accessible roles are mapped, labels match target controls, and media items carry alternative text."
                    )
                )

                # 2. Keyboard Nav Check
                if acc.keyboard_navigation or acc.focus_management:
                    strat_id = f"STRAT-{comp_name}-A11Y-KEYBOARD"
                    strategies.append(
                        TestStrategy(
                            id=strat_id,
                            category="Accessibility Tests",
                            priority=priority,
                            target_component=comp_name,
                            description=f"Verify keyboard navigation focus tab-order flow and key action listeners ({', '.join(acc.keyboard_navigation)}).",
                            preconditions=["Render component and emit keyboard trigger events"],
                            coverage_tags=["a11y", "keyboard"],
                            strategy_id=strat_id,
                            component_id=comp_id,
                            risk=risk_str,
                            reason=reason_str,
                            behavior_reference=f"Focus manager: focus_management={acc.focus_management}, listeners={acc.keyboard_navigation}",
                            test_objective="Assert keyboard-only users can focus, trigger, and navigate layout controls.",
                            expected_outcome=f"Focus trap constraints align, tab indices cycle appropriately, and Enter/Space activate triggers."
                        )
                    )

        return strategies


class ContextStrategyGenerator(BaseStrategyGenerator):
    """Generates Context Provider/Consumer and Redux Store integration strategies."""

    @property
    def category_name(self) -> str:
        return "Event Handling Tests"

    def generate(self, ir: FrameworkAgnosticIR) -> List[TestStrategy]:
        strategies: List[TestStrategy] = []
        for comp in ir.components:
            comp_name = comp.name
            comp_id = comp.id or f"comp_{comp_name}"
            priority = get_priority_by_risk(ir, comp_name)
            risk_str = get_risk_str(ir, comp_name)
            reason_str = get_risk_reason(ir, comp_name)
            
            ctx_usages = getattr(comp, "context_usage", []) or []
            contexts = []
            if comp.data_flow and comp.data_flow.context_used:
                contexts.extend(comp.data_flow.context_used)
            for ctx in ctx_usages:
                contexts.append(ctx.get("context_name"))
            contexts = sorted(list(set(filter(None, contexts))))

            for ctx_name in contexts:
                strat_id = f"STRAT-{comp_name}-CTX-CONSUMER-{ctx_name.upper()}"
                strategies.append(
                    TestStrategy(
                        id=strat_id,
                        category="Event Handling Tests",
                        priority=priority,
                        target_component=comp_name,
                        description=f"Verify {comp_name} consumes Context/Store values from '{ctx_name}' correctly and re-renders on value updates.",
                        preconditions=[f"Wrap component inside mock provider for context: '{ctx_name}'"],
                        coverage_tags=["context", "redux", "store", ctx_name],
                        strategy_id=strat_id,
                        component_id=comp_id,
                        risk=risk_str,
                        reason=reason_str,
                        behavior_reference=f"Context Consumer: {ctx_name}",
                        test_objective=f"Assert component re-renders when context provider updates '{ctx_name}' store value.",
                        expected_outcome="Context updates trigger react updates in child component layout cleanly."
                    )
                )

        return strategies


class HookStrategyGenerator(BaseStrategyGenerator):
    """Generates Hook-specific lifecycle side-effect strategies."""

    @property
    def category_name(self) -> str:
        return "State Management Tests"

    def generate(self, ir: FrameworkAgnosticIR) -> List[TestStrategy]:
        strategies: List[TestStrategy] = []
        for comp in ir.components:
            comp_name = comp.name
            comp_id = comp.id or f"comp_{comp_name}"
            priority = get_priority_by_risk(ir, comp_name)
            risk_str = get_risk_str(ir, comp_name)
            reason_str = get_risk_reason(ir, comp_name)

            hooks = comp.hooks
            if hooks:
                hook_names = [h.name for h in hooks]
                strat_id = f"STRAT-{comp_name}-HOOKS-LIFECYCLE"
                strategies.append(
                    TestStrategy(
                        id=strat_id,
                        category="State Management Tests",
                        priority=priority,
                        target_component=comp_name,
                        description=f"Verify hook lifecycles ({', '.join(hook_names)}) trigger updates, execute side-effects, and clean up on unmount.",
                        preconditions=["Render component with updates to hook dependencies"],
                        coverage_tags=["hooks", "lifecycle"],
                        strategy_id=strat_id,
                        component_id=comp_id,
                        risk=risk_str,
                        reason=reason_str,
                        behavior_reference=f"React hooks: {hook_names}",
                        test_objective="Assert dependency array updates trigger callbacks, and teardown registers cleanup listeners.",
                        expected_outcome="Hook side effects resolve correctly, and component unmount unregisters active listeners."
                    )
                )

        return strategies


def get_unique_comp_id_from_name(ir: FrameworkAgnosticIR, comp_name: str) -> Optional[str]:
    comp = next((c for c in ir.components if c.name == comp_name), None)
    if comp:
        return comp.id
    return f"comp_{comp_name}"
