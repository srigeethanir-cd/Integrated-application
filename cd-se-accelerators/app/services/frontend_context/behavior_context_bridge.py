"""
Behavior Context Bridge.

Transforms FCE SingleComponentFrontendContext objects into behavior-level
test scenarios that the TestCaseGenerator can consume directly.

Each scenario is a structured dict describing:
  component → function/handler → trigger → input → behavior → expected result

Scenarios are generated ONLY from facts present in the FCE extraction.
Nothing is invented.
"""

import logging
from typing import Any, Dict, List, Optional

from app.services.frontend_context.models import (
    FrontendContextResponse,
    SingleComponentFrontendContext,
)

logger = logging.getLogger(__name__)


def _state_initial_display(val: Optional[str]) -> str:
    """Human-readable initial value display."""
    if val is None:
        return "undefined"
    if val == '""' or val == "''":
        return "''"
    return val


def _infer_example_value(state_name: str, state_type: str, initial_value: Optional[str]) -> str:
    """Generate a realistic example value for a state variable based on its name and type."""
    name_lower = state_name.lower()
    if "email" in name_lower:
        return "'user@test.com'"
    if "password" in name_lower:
        return "'SecurePass123'"
    if "name" in name_lower or "username" in name_lower:
        return "'Jane Doe'"
    if "phone" in name_lower:
        return "'+1-555-0100'"
    if "url" in name_lower or "link" in name_lower:
        return "'https://example.com'"
    if "search" in name_lower or "query" in name_lower or "filter" in name_lower:
        return "'search term'"
    if state_type == "boolean" or initial_value in ("false", "true"):
        return "true" if initial_value == "false" else "false"
    if state_type == "number" or (initial_value and initial_value.replace(".", "").isdigit()):
        return "42"
    if state_type == "array" or initial_value == "[]":
        return "[{id: 1}]"
    if state_type == "object" or initial_value == "{}":
        return "{key: 'value'}"
    if state_type == "null" or initial_value == "null":
        return "{id: 1, name: 'Test'}"
    return "'new value'"


class BehaviorContextBridge:
    """Converts FCE ground-truth contexts into behavior-level test scenarios."""

    def generate_scenarios(
        self,
        frontend_context: Optional[FrontendContextResponse],
    ) -> List[Dict[str, Any]]:
        """Generate behavior-level test scenarios from FrontendContext.

        Returns a list of scenario dicts, each suitable for direct test case generation.
        """
        if not frontend_context or not frontend_context.contexts:
            return []

        scenarios: List[Dict[str, Any]] = []

        for ctx in frontend_context.contexts:
            try:
                scenarios.extend(self._generate_state_handler_scenarios(ctx))
                scenarios.extend(self._generate_form_submit_scenarios(ctx))
                scenarios.extend(self._generate_api_scenarios(ctx))
                scenarios.extend(self._generate_conditional_rendering_scenarios(ctx))
                scenarios.extend(self._generate_effect_scenarios(ctx))
                scenarios.extend(self._generate_prop_callback_scenarios(ctx))
                scenarios.extend(self._generate_toggle_scenarios(ctx))
                scenarios.extend(self._generate_general_function_scenarios(ctx, scenarios))
            except Exception as exc:
                logger.warning(
                    "BehaviorContextBridge: Failed to generate scenarios for %s: %s",
                    ctx.component_name, exc,
                )

        logger.info(
            "BehaviorContextBridge: Generated %d behavior scenarios from %d component(s)",
            len(scenarios), len(frontend_context.contexts),
        )
        return scenarios

    # ------------------------------------------------------------------
    # Scenario generators (each returns a list of dicts)
    # ------------------------------------------------------------------

    def _generate_state_handler_scenarios(
        self, ctx: SingleComponentFrontendContext
    ) -> List[Dict[str, Any]]:
        """Generate scenarios for state-updating handler functions."""
        scenarios = []
        comp = ctx.component_name
        src = ctx.source_file

        for fn in ctx.functions:
            if not fn.writes:
                continue

            # Skip form submit handlers — they get their own dedicated scenario
            if "submit" in fn.name.lower():
                continue

            for state_name in fn.writes:
                st = next((s for s in ctx.states if s.name == state_name), None)
                if not st:
                    continue

                setter = st.setter or f"set{state_name.capitalize()}"
                init_val = _state_initial_display(st.initial_value)
                example_val = _infer_example_value(state_name, st.state_type, st.initial_value)

                # Find matching event trigger
                ev = next((e for e in ctx.events if e.handler == fn.name), None)
                trigger_desc = f"{ev.name} on {ev.element_tag}" if ev else f"{fn.name}() invocation"
                input_desc = ", ".join(fn.reads) if fn.reads else "new value"

                scenarios.append({
                    "component": comp,
                    "source_file": src,
                    "function": fn.name,
                    "trigger": trigger_desc,
                    "input": input_desc,
                    "behavior": f"calls {setter}({example_val}) → updates {state_name} state",
                    "category": "State",
                    "test_title": f"Verify {fn.name} updates {state_name} state when user triggers {trigger_desc}",
                    "test_objective": (
                        f"When {trigger_desc} fires, {fn.name} reads {input_desc} "
                        f"and calls {setter}, updating {state_name} from {init_val} to the new value."
                    ),
                    "preconditions": [
                        f"Mount {comp} with default props",
                        f"{state_name} state is {init_val} (initial)",
                    ],
                    "steps": [
                        {"action": f"Render {comp} with default props", "expected": f"{state_name} is {init_val}"},
                        {"action": f"Simulate {trigger_desc} with value {example_val}", "expected": f"{fn.name} is called"},
                        {"action": f"Assert {state_name} state updated to {example_val}", "expected": f"UI reflects {state_name} = {example_val}"},
                        {"action": f"Unmount {comp}", "expected": "No memory leaks or dangling state"},
                    ],
                    "expected_result": f"{state_name} state updates from {init_val} to {example_val}",
                    "why_this_test_matters": (
                        f"Validates that {fn.name} correctly binds {trigger_desc} to {state_name} state "
                        f"via {setter}, ensuring two-way data flow."
                    ),
                })

        return scenarios

    def _generate_form_submit_scenarios(
        self, ctx: SingleComponentFrontendContext
    ) -> List[Dict[str, Any]]:
        """Generate scenarios for form submission handlers."""
        scenarios = []
        comp = ctx.component_name
        src = ctx.source_file

        for fn in ctx.functions:
            if "submit" not in fn.name.lower():
                continue

            ev = next((e for e in ctx.events if e.handler == fn.name), None)
            has_prevent_default = ev.prevent_default if ev else ("event" in " ".join(fn.parameters))

            # Find API call in the function context
            api_call = next((a for a in ctx.api_calls if a.function_name in ("fetch", "axios")), None)
            api_desc = ""
            if api_call:
                api_desc = f" and sends {api_call.http_method} request to {api_call.endpoint or 'API endpoint'}"

            # Find loading/error states
            loading_st = next((s for s in ctx.states if "loading" in s.name.lower()), None)
            error_st = next((s for s in ctx.states if "error" in s.name.lower()), None)

            steps = [
                {"action": f"Render {comp} and fill form fields", "expected": "Form renders with input fields"},
                {"action": f"Simulate form onSubmit event", "expected": f"{'preventDefault is called, ' if has_prevent_default else ''}{fn.name} executes"},
            ]

            if loading_st:
                steps.append(
                    {"action": f"Assert {loading_st.name} is true during submission", "expected": "Loading indicator is visible"}
                )

            if api_call:
                steps.append(
                    {"action": f"Mock {api_call.http_method} {api_call.endpoint or 'API'} to return success", "expected": "API call completes successfully"}
                )

            steps.append(
                {"action": f"Unmount {comp}", "expected": "No memory leaks"}
            )

            scenarios.append({
                "component": comp,
                "source_file": src,
                "function": fn.name,
                "trigger": "onSubmit on form",
                "input": "form field values",
                "behavior": f"prevents default submission{api_desc}",
                "category": "Forms",
                "test_title": f"Verify {fn.name} prevents default and submits form data in {comp}",
                "test_objective": (
                    f"When the form is submitted, {fn.name} calls preventDefault{api_desc}, "
                    f"manages loading state, and handles success/error responses."
                ),
                "preconditions": [
                    f"Mount {comp}",
                    "Form fields are filled with valid data",
                ],
                "steps": steps,
                "expected_result": f"Form submission completes successfully via {fn.name}",
                "why_this_test_matters": (
                    f"Validates the complete form submission flow in {comp}: "
                    f"preventDefault, API communication, loading state management, and error handling."
                ),
            })

            # Generate error path scenario if error state exists
            if error_st and api_call:
                scenarios.append({
                    "component": comp,
                    "source_file": src,
                    "function": fn.name,
                    "trigger": "onSubmit on form (error path)",
                    "input": "form field values",
                    "behavior": f"handles API failure and sets {error_st.name} state",
                    "category": "Forms",
                    "test_title": f"Verify {fn.name} handles API error and displays error message in {comp}",
                    "test_objective": (
                        f"When the {api_call.http_method} {api_call.endpoint or 'API'} call fails, "
                        f"{fn.name} catches the error and sets {error_st.name} state."
                    ),
                    "preconditions": [
                        f"Mount {comp}",
                        f"Mock {api_call.http_method} {api_call.endpoint or 'API'} to return error",
                    ],
                    "steps": [
                        {"action": f"Render {comp} and fill form fields", "expected": "Form renders"},
                        {"action": f"Mock API to reject with 'Invalid credentials'", "expected": "API mock is set"},
                        {"action": "Simulate form onSubmit", "expected": f"{fn.name} catches error"},
                        {"action": f"Assert {error_st.name} state contains error message", "expected": "Error message is displayed to user"},
                    ],
                    "expected_result": f"{error_st.name} state is updated with the error message",
                    "why_this_test_matters": (
                        f"Validates error handling in {fn.name}: API failures must be caught and "
                        f"displayed via {error_st.name} without crashing the UI."
                    ),
                })

        return scenarios

    def _generate_api_scenarios(
        self, ctx: SingleComponentFrontendContext
    ) -> List[Dict[str, Any]]:
        """Generate scenarios for standalone API calls (not in submit handlers)."""
        scenarios = []
        comp = ctx.component_name
        src = ctx.source_file

        for api in ctx.api_calls:
            if api.in_use_effect:
                continue  # Handled by _generate_effect_scenarios

            # Skip if already covered by a submit handler
            submit_fns = {fn.name for fn in ctx.functions if "submit" in fn.name.lower()}
            if submit_fns:
                continue

            scenarios.append({
                "component": comp,
                "source_file": src,
                "function": api.function_name,
                "trigger": f"{api.http_method} {api.endpoint or 'API'} call",
                "input": "request parameters",
                "behavior": f"sends {api.http_method} to {api.endpoint or 'API endpoint'}",
                "category": "API",
                "test_title": f"Verify {api.http_method} {api.endpoint or 'API'} call in {comp}",
                "test_objective": (
                    f"{comp} makes a {api.http_method} request to {api.endpoint or 'API endpoint'}. "
                    f"Verify success response updates component state correctly."
                ),
                "preconditions": [f"Mount {comp}", f"Mock {api.function_name}"],
                "steps": [
                    {"action": f"Render {comp}", "expected": "Component renders"},
                    {"action": f"Mock {api.function_name} {api.http_method} {api.endpoint or 'API'}", "expected": "Mock is configured"},
                    {"action": "Trigger the API call", "expected": "API call is made"},
                    {"action": "Assert state updates from API response", "expected": "Component reflects API data"},
                ],
                "expected_result": f"API call completes and component state is updated",
                "why_this_test_matters": f"Validates the {api.http_method} API integration in {comp}.",
            })

        return scenarios

    def _generate_conditional_rendering_scenarios(
        self, ctx: SingleComponentFrontendContext
    ) -> List[Dict[str, Any]]:
        """Generate scenarios for conditional rendering branches."""
        scenarios = []
        comp = ctx.component_name
        src = ctx.source_file

        for cond in ctx.conditions:
            cond_expr = cond.condition
            rendered = ", ".join(cond.rendered_ui) if cond.rendered_ui else "conditional element"

            scenarios.append({
                "component": comp,
                "source_file": src,
                "function": "render",
                "trigger": f"condition: {cond_expr}",
                "input": ", ".join(cond.dependent_state) if cond.dependent_state else cond_expr,
                "behavior": f"renders {rendered} when {cond_expr} is truthy",
                "category": "Rendering",
                "test_title": f"Verify {rendered} renders when {cond_expr} is truthy in {comp}",
                "test_objective": (
                    f"When {cond_expr} evaluates to true, {comp} should render {rendered}. "
                    f"When false, it should not be present in the DOM."
                ),
                "preconditions": [f"Mount {comp}"],
                "steps": [
                    {"action": f"Render {comp} with {cond_expr} = falsy", "expected": f"{rendered} is not in DOM"},
                    {"action": f"Update state so {cond_expr} = truthy", "expected": f"{rendered} appears in DOM"},
                    {"action": f"Verify {rendered} content", "expected": "Content is correct"},
                    {"action": f"Unmount {comp}", "expected": "Clean unmount"},
                ],
                "expected_result": f"{rendered} is conditionally rendered based on {cond_expr}",
                "why_this_test_matters": (
                    f"Validates conditional rendering logic: {cond_expr} must control "
                    f"whether {rendered} is visible, preventing stale UI."
                ),
            })

        return scenarios

    def _generate_effect_scenarios(
        self, ctx: SingleComponentFrontendContext
    ) -> List[Dict[str, Any]]:
        """Generate scenarios for useEffect data fetching."""
        scenarios = []
        comp = ctx.component_name
        src = ctx.source_file

        for api in ctx.api_calls:
            if not api.in_use_effect:
                continue

            # Find the state that gets updated from this API data
            data_state = next(
                (s for s in ctx.states if s.state_type in ("null", "object", "array")),
                None,
            )
            state_name = data_state.name if data_state else "data"

            scenarios.append({
                "component": comp,
                "source_file": src,
                "function": "useEffect",
                "trigger": f"component mount (useEffect)",
                "input": "dependency props",
                "behavior": f"fetches {api.endpoint or 'data'} and sets {state_name} state",
                "category": "Effects",
                "test_title": f"Verify useEffect fetches {api.endpoint or 'data'} on mount in {comp}",
                "test_objective": (
                    f"On mount, {comp}'s useEffect calls {api.function_name} "
                    f"{api.http_method} {api.endpoint or 'API'} and updates {state_name} state."
                ),
                "preconditions": [
                    f"Mock {api.function_name} {api.endpoint or 'API'}",
                    f"Render {comp} with required props",
                ],
                "steps": [
                    {"action": f"Mock {api.function_name} to return test data", "expected": "Mock is configured"},
                    {"action": f"Render {comp}", "expected": f"useEffect triggers {api.function_name} call"},
                    {"action": f"Wait for async resolution", "expected": f"{state_name} state is updated"},
                    {"action": f"Assert {state_name} reflects API response data", "expected": f"UI displays {state_name} data"},
                ],
                "expected_result": f"{state_name} is populated from {api.endpoint or 'API'} response",
                "why_this_test_matters": (
                    f"Validates that {comp} fetches required data on mount via useEffect "
                    f"and correctly updates {state_name} for rendering."
                ),
            })

        return scenarios

    def _generate_prop_callback_scenarios(
        self, ctx: SingleComponentFrontendContext
    ) -> List[Dict[str, Any]]:
        """Generate scenarios for props that are callback functions."""
        scenarios = []
        comp = ctx.component_name
        src = ctx.source_file

        callback_props = [p for p in ctx.props if p.name.startswith("on") and p.name[2:3].isupper()]

        for prop in callback_props:
            # Find a function that calls this prop
            calling_fn = next(
                (fn for fn in ctx.functions if prop.name in " ".join(fn.reads + fn.writes + [fn.behavior])),
                None,
            )

            scenarios.append({
                "component": comp,
                "source_file": src,
                "function": calling_fn.name if calling_fn else f"handler for {prop.name}",
                "trigger": f"{prop.name} callback invocation",
                "input": "callback arguments",
                "behavior": f"invokes {prop.name} prop callback",
                "category": "Props",
                "test_title": f"Verify {prop.name} callback is invoked in {comp}",
                "test_objective": (
                    f"When the appropriate action triggers {prop.name}, {comp} must invoke "
                    f"the callback function passed via the {prop.name} prop."
                ),
                "preconditions": [
                    f"Mount {comp} with jest.fn() for {prop.name}",
                ],
                "steps": [
                    {"action": f"Render {comp} with {prop.name}={{jest.fn()}}", "expected": "Component renders"},
                    {"action": f"Trigger action that invokes {prop.name}", "expected": f"{prop.name} callback is called"},
                    {"action": f"Assert {prop.name} was called with correct arguments", "expected": "Arguments match expected values"},
                    {"action": f"Unmount {comp}", "expected": "Clean unmount"},
                ],
                "expected_result": f"{prop.name} callback is invoked with correct arguments",
                "why_this_test_matters": (
                    f"Validates that {comp} correctly invokes the {prop.name} parent callback, "
                    f"ensuring proper parent-child communication."
                ),
            })

        return scenarios

    def _generate_toggle_scenarios(
        self, ctx: SingleComponentFrontendContext
    ) -> List[Dict[str, Any]]:
        """Generate scenarios for boolean toggle handlers."""
        scenarios = []
        comp = ctx.component_name
        src = ctx.source_file

        for fn in ctx.functions:
            fn_lower = fn.name.lower()
            if "toggle" not in fn_lower:
                continue

            # Find the boolean state being toggled
            toggled_state = None
            for state_name in fn.writes:
                st = next((s for s in ctx.states if s.name == state_name), None)
                if st and (st.state_type == "boolean" or st.initial_value in ("false", "true")):
                    toggled_state = st
                    break

            if not toggled_state:
                continue

            ev = next((e for e in ctx.events if e.handler == fn.name), None)
            trigger_desc = f"{ev.name} on {ev.element_tag}" if ev else f"click on toggle button"

            scenarios.append({
                "component": comp,
                "source_file": src,
                "function": fn.name,
                "trigger": trigger_desc,
                "input": "current state value",
                "behavior": f"toggles {toggled_state.name} from {toggled_state.initial_value} to {_infer_example_value(toggled_state.name, toggled_state.state_type, toggled_state.initial_value)}",
                "category": "State",
                "test_title": f"Verify {fn.name} toggles {toggled_state.name} state in {comp}",
                "test_objective": (
                    f"When {trigger_desc} fires, {fn.name} toggles {toggled_state.name} "
                    f"from {toggled_state.initial_value} to the opposite boolean value."
                ),
                "preconditions": [
                    f"Mount {comp}",
                    f"{toggled_state.name} is {toggled_state.initial_value} (initial)",
                ],
                "steps": [
                    {"action": f"Render {comp}", "expected": f"{toggled_state.name} is {toggled_state.initial_value}"},
                    {"action": f"Simulate {trigger_desc}", "expected": f"{toggled_state.name} toggles to opposite value"},
                    {"action": f"Simulate {trigger_desc} again", "expected": f"{toggled_state.name} toggles back to {toggled_state.initial_value}"},
                    {"action": f"Unmount {comp}", "expected": "Clean unmount"},
                ],
                "expected_result": f"{toggled_state.name} toggles between true and false on each {trigger_desc}",
                "why_this_test_matters": (
                    f"Validates toggle behavior: {fn.name} must flip {toggled_state.name} "
                    f"on every invocation, controlling conditional UI rendering."
                ),
            })

        return scenarios

    def _generate_general_function_scenarios(
        self, ctx: SingleComponentFrontendContext, existing_scenarios: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Generate scenarios for all other functions/handlers not covered by specialized generators."""
        scenarios = []
        comp = ctx.component_name
        src = ctx.source_file
        covered_fns = {s.get("function") for s in existing_scenarios if s.get("function")}

        for fn in ctx.functions:
            if fn.name in covered_fns:
                continue

            ev = next((e for e in ctx.events if e.handler == fn.name), None)
            trigger_desc = f"{ev.name} on {ev.element_tag}" if ev else f"{fn.name}() invocation"
            input_desc = ", ".join(fn.parameters) if fn.parameters else ("reads " + ", ".join(fn.reads) if fn.reads else "default arguments")
            behavior_desc = fn.behavior or (f"updates {', '.join(fn.writes)}" if fn.writes else f"executes {fn.name}")

            cat = "Events" if ("click" in fn.name.lower() or "handle" in fn.name.lower()) else "State"

            scenarios.append({
                "component": comp,
                "source_file": src,
                "function": fn.name,
                "trigger": trigger_desc,
                "input": input_desc,
                "behavior": behavior_desc,
                "category": cat,
                "test_title": f"Verify {fn.name} executes correctly when triggered by {trigger_desc} in {comp}",
                "test_objective": (
                    f"When {trigger_desc} occurs, {fn.name} receives {input_desc} and {behavior_desc}."
                ),
                "preconditions": [
                    f"Mount {comp} with required props",
                ],
                "steps": [
                    {"action": f"Render {comp}", "expected": "Component mounts in DOM"},
                    {"action": f"Trigger {trigger_desc}", "expected": f"{fn.name} is invoked"},
                    {"action": f"Verify component updates", "expected": f"{behavior_desc} succeeds"},
                    {"action": f"Unmount {comp}", "expected": "Clean unmount"},
                ],
                "expected_result": f"{fn.name} executes without error and updates component state",
                "why_this_test_matters": (
                    f"Validates that {fn.name} in {comp} processes {trigger_desc} properly."
                ),
            })

        return scenarios

