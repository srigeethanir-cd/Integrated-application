"""
React IR Mapper – Module 4.

Maps React / Next.js parser output from Module 3 into a framework-agnostic IR.

Normalizations:
- React Component → ComponentIR
- React JSX Element → UIElement
- React useState / state → ComponentState
- React onClick/onChange/onSubmit → UIEvent
- React fetch/axios/service → ServiceDependency
- Imports → Dependencies
- Existing Tests → ExistingTestModel
"""

import logging
from typing import Any, Dict, List, Set
from app.models.ir_models import (
    ComponentIR,
    ComponentState,
    ExistingTestModel,
    FrameworkAgnosticIR,
    ServiceDependency,
    UIElement,
    UIEvent,
    FormModel,
    FormField,
    RouteModel,
    HookInfo,
    InteractionGraphNode,
    StateTransition,
    RenderCondition,
    DataFlowInfo,
    AccessibilityDetail,
    RiskAnalysis,
    ComponentTestability,
)
from app.models.analyzer_models import (
    AccessibilityInfo,
    TestingMetadata,
    DependencyNode,
    TestMapping,
    ComponentRelationshipInfo,
)
from app.services.ir_generator.base_mapper import BaseIRMapper

logger = logging.getLogger(__name__)


def generate_rtl_locator(tag: str, elem_id: str | None, role: str | None, aria_label: str | None, placeholder: str | None, alt: str | None) -> str:
    """Generate preferred React Testing Library locator string."""
    if aria_label:
        return f"screen.getByLabelText({repr(aria_label)})"
    if placeholder:
        return f"screen.getByPlaceholderText({repr(placeholder)})"
    if alt:
        return f"screen.getByAltText({repr(alt)})"
    if role:
        return f"screen.getByRole({repr(role)})"
    # Semantic tag defaults
    if tag == "button":
        return "screen.getByRole('button')"
    if tag == "a":
        return "screen.getByRole('link')"
    if tag == "input":
        return "screen.getByRole('textbox')"
    if tag == "img":
        return "screen.getByRole('img')"
    if elem_id:
        return f"container.querySelector('#{elem_id}')"
    return f"container.querySelector('{tag}')"


def generate_angular_locator(tag: str, elem_id: str | None, role: str | None, aria_label: str | None, placeholder: str | None, alt: str | None) -> str:
    """Generate preferred Angular TestBed css locator string."""
    if aria_label:
        return f"by.css('[aria-label=\"{aria_label}\"]')"
    if elem_id:
        return f"by.css('#{elem_id}')"
    if placeholder:
        return f"by.css('[placeholder=\"{placeholder}\"]')"
    if alt:
        return f"by.css('[alt=\"{alt}\"]')"
    if role:
        return f"by.css('[role=\"{role}\"]')"
    return f"by.css('{tag}')"


class ReactIRMapper(BaseIRMapper):
    """Mapper implementation for React and Next.js applications."""

    @property
    def framework_name(self) -> str:
        return "React"

    def map_to_ir(self, analysis_data: Dict[str, Any], project_name: str = "IngestedProject") -> FrameworkAgnosticIR:
        logger.info("ReactIRMapper: mapping analysis output to framework-agnostic IR")

        raw_analysis = analysis_data.get("analysis", {})
        if not isinstance(raw_analysis, dict):
            raw_analysis = analysis_data

        components_raw = raw_analysis.get("components", [])
        tests_raw = raw_analysis.get("existing_tests", [])

        # Read top level collection fields
        component_relationships_raw = raw_analysis.get("component_relationships", [])
        dependency_graph_raw = raw_analysis.get("dependency_graph", [])
        test_mapping_raw = raw_analysis.get("test_mapping", [])

        ir_components: List[ComponentIR] = []
        ir_elements: List[UIElement] = []
        ir_events: List[UIEvent] = []
        ir_state: List[ComponentState] = []
        ir_services: List[ServiceDependency] = []
        ir_routes: List[RouteModel] = []
        ir_dependencies: List[Dict[str, Any]] = []
        ir_forms: List[FormModel] = []

        seen_deps = set()

        # Helper to compute normalized unique ID from component name + path
        def get_unique_comp_id(c_name: str) -> str:
            match = next((c for c in components_raw if c.get("name") == c_name), None)
            if match:
                m_path = match.get("file_path", "").replace("\\", "/").strip("/")
                return f"comp_{m_path}_{c_name}".replace("/", "_").replace(".", "_").replace("-", "_")
            return f"comp_{c_name}"

        for comp in components_raw:
            comp_name = comp.get("name", "UnknownComponent")
            file_path = comp.get("file_path", "")
            comp_type = comp.get("type", "functional")
            comp_id = get_unique_comp_id(comp_name)

            # Compute parent / children depth mapping
            rel = next((r for r in component_relationships_raw if r.get("component") == comp_name), {})
            parent_name = rel.get("parent")
            parent_id = get_unique_comp_id(parent_name) if parent_name else None
            children_names = rel.get("children", [])
            children_ids = [get_unique_comp_id(c) for c in children_names]
            depth = rel.get("depth", 0)

            # Compute accessibility metadata model
            acc_raw = comp.get("accessibility")
            accessibility = None
            if acc_raw:
                accessibility = AccessibilityInfo(
                    aria_attributes=acc_raw.get("aria_attributes", {}),
                    roles=acc_raw.get("roles", []),
                    keyboard_events=acc_raw.get("keyboard_events", []),
                    has_focus_management=acc_raw.get("has_focus_management", False),
                    alt_texts=acc_raw.get("alt_texts", []),
                    label_associations=acc_raw.get("label_associations", []),
                    accessible_elements=acc_raw.get("accessible_elements", [])
                )

            # Compute testing metadata model
            tm_raw = comp.get("testing_metadata")
            testing_metadata = None
            if tm_raw:
                testing_metadata = TestingMetadata(
                    testable_elements=tm_raw.get("testable_elements", []),
                    interactive_elements=tm_raw.get("interactive_elements", []),
                    mock_dependencies=tm_raw.get("mock_dependencies", []),
                    recommended_test_categories=tm_raw.get("recommended_test_categories", []),
                    recommended_queries=[dict(q) for q in tm_raw.get("recommended_queries", [])],
                    edge_cases=tm_raw.get("edge_cases", []),
                    negative_scenarios=tm_raw.get("negative_scenarios", []),
                    suggested_mocks=[dict(m) for m in tm_raw.get("suggested_mocks", [])]
                )

            # Compute dependency graph node model (fully preserving imports_hooks, imports_stores, imports_external_libraries)
            dg_raw = comp.get("dependency_graph")
            dependency_graph = None
            if dg_raw:
                dependency_graph = DependencyNode(
                    component=dg_raw.get("component", comp_name),
                    imports_components=dg_raw.get("imports_components", []),
                    imports_services=dg_raw.get("imports_services", []),
                    imports_utilities=dg_raw.get("imports_utilities", []),
                    imports_contexts=dg_raw.get("imports_contexts", []),
                    imports_hooks=dg_raw.get("imports_hooks", []),
                    imports_stores=dg_raw.get("imports_stores", []),
                    imports_external_libraries=dg_raw.get("imports_external_libraries", [])
                )

            # Map form elements inside component
            comp_forms = []
            for form in comp.get("forms", []):
                form_name = form.get("library") or "form"
                form_id = f"form_{comp_id}_{form_name}"
                
                fields = []
                for idx, field in enumerate(form.get("fields", [])):
                    field_name = field.get("name", f"input_{idx}")
                    field_id = f"field_{comp_id}_{form_name}_{field_name}"
                    fields.append(
                        FormField(
                            name=field_name,
                            type=field.get("field_type", "control"),
                            validators=field.get("validation_rules", []),
                            id=field_id,
                            is_controlled=field.get("is_controlled", False),
                            is_required=field.get("is_required", False),
                            validation_rules=field.get("validation_rules", [])
                        )
                    )
                
                fm = FormModel(
                    name=form_name,
                    component_name=comp_name,
                    controls=fields,
                    validators=[],
                    id=form_id,
                    element=form.get("element", "form"),
                    is_controlled=form.get("is_controlled", False),
                    submit_handler=form.get("submit_handler"),
                    reset_handler=form.get("reset_handler"),
                    library=form.get("library")
                )
                comp_forms.append(fm)
                ir_forms.append(fm)

            # Dynamic Risk Analysis Calculation
            calculated_risk = 1
            risk_reasons: List[str] = []

            has_use_effect = any(h.get("name") == "useEffect" for h in comp.get("hooks", [])) or "useEffect" in str(comp)
            if has_use_effect:
                calculated_risk += 2
                risk_reasons.append("Contains side-effect hooks (useEffect)")

            if comp.get("api_calls"):
                calculated_risk += 2
                risk_reasons.append("Executes external API service calls")

            is_async = any("async" in str(eh) for eh in comp.get("event_handlers", [])) or bool(comp.get("api_calls"))
            if is_async:
                calculated_risk += 2
                risk_reasons.append("Handles asynchronous operations or promises")

            rt_info = comp.get("routing_info") or {}
            if rt_info.get("uses_navigate") or rt_info.get("links") or rt_info.get("routes"):
                calculated_risk += 2
                risk_reasons.append("Integrates with router / navigation")

            if comp.get("state"):
                calculated_risk += 1
                risk_reasons.append("Manages reactive component state")

            if comp.get("conditional_rendering") or "&&" in str(comp.get("jsx_elements", [])):
                calculated_risk += 1
                risk_reasons.append("Contains conditional UI rendering logic")

            if comp_forms:
                calculated_risk += 1
                risk_reasons.append("Processes form inputs and validation")

            uses_context = any(h.get("name") == "useContext" for h in comp.get("hooks", [])) or "Context" in str(comp)
            if uses_context:
                calculated_risk += 2
                risk_reasons.append("Consumes React Context provider")

            acc_raw_data = comp.get("accessibility", {})
            has_missing_acc = bool(acc_raw_data.get("missing_accessibility") or acc_raw_data.get("warnings"))
            if has_missing_acc:
                calculated_risk += 1
                risk_reasons.append("Identified WCAG accessibility gaps")

            if len(comp.get("event_handlers", [])) > 2:
                calculated_risk += 2
                risk_reasons.append("Handles multiple interactive user events")

            final_risk_score = min(10, calculated_risk)
            if final_risk_score <= 3:
                risk_level = "Low"
            elif final_risk_score <= 6:
                risk_level = "Medium"
            else:
                risk_level = "High"

            risk_analysis_obj = RiskAnalysis(
                score=final_risk_score,
                level=risk_level,
                risk_reasons=risk_reasons
            )

            # Extract Hooks Info
            extracted_hooks: List[HookInfo] = []
            for hk in comp.get("hooks", []):
                h_name = hk.get("name", "useHook")
                extracted_hooks.append(
                    HookInfo(
                        name=h_name,
                        purpose=hk.get("purpose", f"Manage component logic via {h_name}"),
                        dependencies=hk.get("dependencies", []),
                        cleanup=hk.get("cleanup", False),
                        side_effects=hk.get("side_effects", [])
                    )
                )

            # Interaction Graph
            interaction_graph: List[InteractionGraphNode] = []
            existing_handlers = set()
            for eh in comp.get("event_handlers", []):
                h_name = eh.get("name", "handler")
                ev_type = eh.get("event_type", "onClick")
                action_desc = f"Interact with {eh.get('element', 'element')} trigger {ev_type}"
                st_update = ", ".join(eh.get("updates_state", [])) or None
                
                effects = []
                if eh.get("updates_state"):
                    effects.append(f"updates state: {', '.join(eh.get('updates_state'))}")
                if eh.get("service_calls"):
                    effects.append(f"calls API: {', '.join(eh.get('service_calls'))}")
                if eh.get("navigation"):
                    effects.append("triggers client-side navigation")
                
                business_effect = " & ".join(effects).capitalize() if effects else "Triggers presentational UI updates"
                
                interaction_graph.append(
                    InteractionGraphNode(
                        user_action=action_desc,
                        event=ev_type,
                        handler=h_name,
                        state_update=st_update,
                        dom_change=f"Updates DOM for {comp_name}",
                        business_effect=business_effect
                    )
                )
                existing_handlers.add(h_name)

            # Ensure all AST functions (e.g. handleSubmit, handlePasswordChange, handleSave) are represented in interaction_graph
            for fn in comp.get("functions", []):
                fn_name = fn.get("name") if isinstance(fn, dict) else str(fn)
                if fn_name and fn_name not in existing_handlers and not fn_name.startswith("use"):
                    action_desc = f"Execute function {fn_name}()"
                    ev_type = "submit" if "submit" in fn_name.lower() else "change" if "change" in fn_name.lower() else "click"
                    interaction_graph.append(
                        InteractionGraphNode(
                            user_action=action_desc,
                            event=ev_type,
                            handler=fn_name,
                            state_update="Mutates internal component state",
                            dom_change=f"Updates DOM for {comp_name}",
                            business_effect=f"Executes component method {fn_name}()"
                        )
                    )
                    existing_handlers.add(fn_name)

            # State Transitions Graph
            state_transitions: List[StateTransition] = []
            for st in comp.get("state", []):
                st_name = st.get("name", "state")
                init_val = str(st.get("initial_value", "false"))
                next_val = "true" if init_val in ["false", "0", "null", "''"] else "updated_value"
                upd_by = ", ".join(st.get("updated_by", ["user_interaction"]))
                
                affected_ids = []
                for u_tag in st.get("used_in", []):
                    for idx, jsx in enumerate(comp.get("jsx_elements", [])):
                        if jsx.get("tag") == u_tag:
                            affected_ids.append(f"elem_{comp_id}_{u_tag}_{idx}")
                if not affected_ids:
                    affected_ids = [comp_id]
                    
                state_transitions.append(
                    StateTransition(
                        current_state=f"{st_name} = {init_val}",
                        trigger=f"Triggered by {upd_by}",
                        next_state=f"{st_name} = {next_val}",
                        affected_elements=affected_ids
                    )
                )

            # Render Conditions
            render_conditions: List[RenderCondition] = []
            for cr in comp.get("conditional_rendering", []):
                cond_expr = cr.get("condition", "isCondition")
                dependent_state = [st.get("name") for st in comp.get("state", []) if st.get("name") in cond_expr]
                affected_ui = []
                consequent = cr.get("consequent")
                if consequent and consequent != "null" and consequent != "JSX":
                    affected_ui.append(consequent)
                alternate = cr.get("alternate")
                if alternate and alternate != "null" and alternate != "JSX":
                    affected_ui.append(alternate)
                if not affected_ui:
                    affected_ui = [comp_name]
                
                visibility_rule = f"Render {consequent or 'UI'} when {cond_expr} is truthy"
                if alternate and alternate != "null":
                    visibility_rule += f", otherwise render {alternate}"
                
                render_conditions.append(
                    RenderCondition(
                        condition=cond_expr,
                        dependent_state=dependent_state,
                        affected_ui=affected_ui,
                        visibility_rule=visibility_rule
                    )
                )

            # Data Flow
            props_to_state = []
            for p in comp.get("props", []):
                p_name = p.get("name")
                for st in comp.get("state", []):
                    init_val = st.get("initial_value")
                    if init_val and p_name in init_val:
                        props_to_state.append({"prop": p_name, "state": st.get("name")})

            state_to_derived = []
            for hk in comp.get("hooks", []):
                if hk.get("name") == "useMemo":
                    deps = hk.get("dependencies", [])
                    for dep in deps:
                        for st in comp.get("state", []):
                            if st.get("name") in dep:
                                state_to_derived.append({"state": st.get("name"), "derived": hk.get("purpose", "derived_value")})

            prop_drilling = []
            for jsx in comp.get("jsx_elements", []):
                tag = jsx.get("tag", "")
                if tag[0].isupper() and tag not in ["Fragment", "React.Fragment"]:
                    for attr in jsx.get("attributes", []):
                        for p in comp.get("props", []):
                            p_name = p.get("name")
                            if p_name == attr:
                                prop_drilling.append(p_name)

            data_flow_obj = DataFlowInfo(
                props_to_state=props_to_state,
                state_to_derived=state_to_derived,
                prop_drilling=prop_drilling,
                context_used=[ctx.get("context_name") for ctx in comp.get("context_usage", [])],
                api_response_used=[api.get("function_name") for api in comp.get("api_calls", [])],
                memoized_values=[hk.get("name") for hk in comp.get("hooks", []) if hk.get("name") in ["useMemo", "useCallback"]]
            )

            # Accessibility Detail
            aria_roles = []
            labels = []
            alt_texts = []
            keyboard_navigation = []
            focus_mgmt = None
            tab_order = "Default tab index"
            
            if acc_raw:
                aria_roles = acc_raw.get("roles", [])
                labels = list(acc_raw.get("label_associations", []))
                for k, v in acc_raw.get("aria_attributes", {}).items():
                    if k in ("aria-label", "aria-labelledby") and v:
                        labels.append(v)
                keyboard_navigation = acc_raw.get("keyboard_events", [])
                focus_mgmt = "Managed (focus() or autoFocus detected)" if acc_raw.get("has_focus_management") else None
                alt_texts = acc_raw.get("alt_texts", [])
                
            acc_detail_obj = AccessibilityDetail(
                aria_roles=aria_roles,
                labels=labels,
                keyboard_navigation=keyboard_navigation,
                focus_management=focus_mgmt,
                tab_order=tab_order,
                alt_text=alt_texts,
                missing_accessibility=[]
            )
            
            warnings = []
            for jsx in comp.get("jsx_elements", []):
                tag = jsx.get("tag")
                attrs = jsx.get("attributes", [])
                if tag == "img" and "alt" not in attrs:
                    warnings.append(f"Image element missing alt attribute.")
                if tag == "button" and not any(a in attrs for a in ["aria-label", "aria-labelledby"]) and not jsx.get("children_count"):
                    warnings.append("Button element missing accessible name or label.")
            acc_detail_obj.missing_accessibility = warnings

            # Testability Metadata Queries & Mocks
            rec_queries = []
            for jsx in comp.get("jsx_elements", []):
                if jsx.get("aria_label"): rec_queries.append("getByLabelText")
                elif jsx.get("placeholder"): rec_queries.append("getByPlaceholderText")
                elif jsx.get("alt"): rec_queries.append("getByAltText")
                elif jsx.get("id"): rec_queries.append("getByTestId")
                elif jsx.get("role"): rec_queries.append("getByRole")
            if not rec_queries:
                rec_queries = ["getByRole", "getByText"]
            rec_queries = sorted(list(set(rec_queries)))

            mock_deps = []
            if dg_raw:
                mock_deps.extend(dg_raw.get("imports_services", []))
                mock_deps.extend(dg_raw.get("imports_hooks", []))
            for api in comp.get("api_calls", []):
                mock_deps.append(api.get("function_name"))
            mock_deps = sorted(list(set(mock_deps)))

            testability_obj = ComponentTestability(
                rendering=[f"Mount test for {comp_name}"],
                state=[f"Verify state {st.get('name')} transitions" for st in comp.get("state", [])],
                props=[f"Props rendering validation for {p.get('name')}" for p in comp.get("props", [])],
                events=[f"Event handler test for {eh.get('name')}" for eh in comp.get("event_handlers", [])],
                accessibility=["WCAG accessibility audit"],
                hooks=[f"Hook test for {h.get('name')}" for h in comp.get("hooks", [])],
                conditional_rendering=[f"Branch test for {cr.get('condition')}" for cr in comp.get("conditional_rendering", [])],
                error_handling=["Error boundary test"],
                async_behavior=["Async resolution test"] if is_async else [],
                integration=[f"Child component integration for {child}" for child in children_names],
                performance=["Re-render performance test"],
                regression=[f"Core regression path for {comp_name}"],
                mock_dependencies=mock_deps,
                recommended_rtl_queries=rec_queries,
                preferred_assertions=["toBeInTheDocument", "toHaveBeenCalled", "toHaveValue"],
                mock_requirements=["Mock API responses and Router providers"]
            )

            # Behavior Summary
            summary_parts = []
            if comp.get("state"):
                st_names = ", ".join([s.get("name") for s in comp.get("state", [])])
                summary_parts.append(f"Manages local reactive state ({st_names}).")
            if comp.get("event_handlers"):
                eh_names = ", ".join([eh.get("name") for eh in comp.get("event_handlers", [])])
                summary_parts.append(f"Handles user interactions via ({eh_names}).")
            if comp.get("api_calls"):
                summary_parts.append("Executes external service API calls.")
            if render_conditions:
                summary_parts.append("Contains conditional rendering rules.")
            if not summary_parts:
                summary_parts.append("Presentational component rendering UI elements.")
            behavior_summary_str = f"The '{comp_name}' component: " + " ".join(summary_parts)

            # 1. Normalize Component
            props_list = comp.get("props", [])
            proj_id_val = analysis_data.get("project_id")
            run_id_val = analysis_data.get("pipeline_run_id")
            ir_components.append(
                ComponentIR(
                    name=comp_name,
                    file_path=file_path,
                    type=comp_type,
                    props_inputs=props_list,
                    outputs_events=[],
                    id=comp_id,
                    project_id=proj_id_val,
                    pipeline_run_id=run_id_val,
                    source_file=file_path,
                    parent=parent_name,
                    parent_id=parent_id,
                    children=children_names,
                    children_ids=children_ids,
                    depth=depth,
                    risk_score=float(final_risk_score),
                    accessibility=accessibility,
                    testing_metadata=testing_metadata,
                    dependency_graph=dependency_graph,
                    forms=comp_forms,
                    hooks=extracted_hooks,
                    interaction_graph=interaction_graph,
                    state_transitions=state_transitions,
                    render_conditions=render_conditions,
                    data_flow=data_flow_obj,
                    accessibility_detail=acc_detail_obj,
                    risk_analysis=risk_analysis_obj,
                    testability=testability_obj,
                    behavior_summary=behavior_summary_str
                )
            )

            # 2. Normalize JSX Elements -> UIElement
            for idx, jsx in enumerate(comp.get("jsx_elements", [])):
                tag = jsx.get("tag", "unknown")
                elem_id = jsx.get("id")
                role = jsx.get("role")
                aria_label = jsx.get("aria_label")
                placeholder = jsx.get("placeholder")
                alt = jsx.get("alt")
                disabled = jsx.get("disabled")

                element_id = f"elem_{comp_id}_{tag}_{idx}"

                rtl_loc = generate_rtl_locator(tag, elem_id, role, aria_label, placeholder, alt)
                ang_loc = generate_angular_locator(tag, elem_id, role, aria_label, placeholder, alt)
                fallback_loc = f"#{elem_id}" if elem_id else tag

                hints = ["Visible"]
                if disabled and disabled != "false":
                    hints.append("Hidden")
                if tag in ["input", "textarea", "select"]:
                    hints.append("State updated")
                if tag in ["button", "a"] or jsx.get("event_bindings"):
                    hints.append("Callback invoked")
                if tag == "form":
                    hints.append("API called")

                ir_elements.append(
                    UIElement(
                        tag=tag,
                        component_name=comp_name,
                        attributes=jsx.get("attributes", []),
                        children_count=jsx.get("children_count", 0),
                        id=element_id,
                        class_name=jsx.get("class_name"),
                        role=role,
                        aria_label=aria_label,
                        aria_expanded=jsx.get("aria_expanded"),
                        placeholder=placeholder,
                        alt=alt,
                        disabled=disabled,
                        required=jsx.get("required"),
                        value_binding=jsx.get("value_binding"),
                        event_bindings=jsx.get("event_bindings", []),
                        locator_rtl=rtl_loc,
                        locator_angular=ang_loc,
                        locator_fallback=fallback_loc,
                        assertion_hints=hints
                    )
                )

            # 3. Normalize Event Handlers -> UIEvent
            for eh in comp.get("event_handlers", []):
                event_attr = eh.get("event_type", "onClick")
                normalized_event_type = event_attr.lower().removeprefix("on")
                handler_name = eh.get("name", "handler")

                event_id = f"evt_{comp_id}_{handler_name}_{normalized_event_type}"

                target_tag = eh.get("element")
                target_element_id = None
                if target_tag:
                    for el in ir_elements:
                        if el.component_name == comp_name and el.tag == target_tag:
                            target_element_id = el.id
                            break

                updates_states = [f"state_{comp_id}_{s}" for s in eh.get("updates_state", [])]

                hints = ["Callback invoked"]
                if updates_states:
                    hints.append("State updated")
                if eh.get("service_calls"):
                    hints.append("API called")
                if eh.get("navigation"):
                    hints.append("Navigation")

                ir_events.append(
                    UIEvent(
                        name=event_attr,
                        event_type=normalized_event_type,
                        component_name=comp_name,
                        handler_name=handler_name,
                        id=event_id,
                        target_element_id=target_element_id,
                        updates_states=updates_states,
                        service_calls=eh.get("service_calls", []),
                        navigation=eh.get("navigation", False),
                        prevent_default=eh.get("prevent_default", False),
                        stop_propagation=eh.get("stop_propagation", False),
                        assertion_hints=hints
                    )
                )

            # 4. Normalize State (useState & class state) -> ComponentState
            for st in comp.get("state", []):
                state_name = st.get("name", "stateVar")
                state_id = f"state_{comp_id}_{state_name}"

                used_by = []
                for u_tag in st.get("used_in", []):
                    for el in ir_elements:
                        if el.component_name == comp_name and el.tag == u_tag:
                            used_by.append(el.id)
                            break

                updated_by = []
                for h_name in st.get("updated_by", []):
                    for ev in ir_events:
                        if ev.component_name == comp_name and ev.handler_name == h_name:
                            updated_by.append(ev.id)
                            break

                ir_state.append(
                    ComponentState(
                        name=state_name,
                        component_name=comp_name,
                        type="hook" if comp_type == "functional" else "state",
                        initial_value=st.get("initial_value"),
                        setter=st.get("setter"),
                        id=state_id,
                        state_type=st.get("state_type", "unknown"),
                        used_by_elements=used_by,
                        updated_by_events=updated_by
                    )
                )

            # 5. Normalize API/Service Calls -> ServiceDependency
            for api in comp.get("api_calls", []):
                fn_name = api.get("function_name", "apiCall")
                call_type = api.get("type", "service_call")
                svc_id = f"svc_{comp_id}_{fn_name}"
                ir_services.append(
                    ServiceDependency(
                        name=fn_name,
                        component_name=comp_name,
                        type=call_type,
                        methods=[fn_name],
                        id=svc_id,
                        api_calls=[api]
                    )
                )

            # 6. RouteModel from routing_info
            rt = comp.get("routing_info")
            if rt:
                for idx, path in enumerate(rt.get("routes", [])):
                    route_id = f"route_{comp_id}_{idx}"
                    ir_routes.append(
                        RouteModel(
                            path=path,
                            component=comp_name,
                            guard=None,
                            lazy_loaded=False,
                            id=route_id,
                            redirects=rt.get("redirects", []),
                            route_params=rt.get("route_params", [])
                        )
                    )

            # 7. Normalize Imports -> Dependencies
            for imp in comp.get("imports", []):
                src = imp.get("source", "")
                if src and src not in seen_deps:
                    seen_deps.add(src)
                    ir_dependencies.append(
                        {
                            "source": src,
                            "specifiers": imp.get("specifiers", []),
                            "is_default": imp.get("is_default", False),
                        }
                    )

        # 8. Normalize Existing Tests -> ExistingTestModel
        ir_tests: List[ExistingTestModel] = [
            ExistingTestModel(file_path=t.get("file_path", ""), type=t.get("type", "test"))
            for t in tests_raw
        ]

        # 9. Top-level mapping collections
        component_relationships = [
            ComponentRelationshipInfo(
                component=r.get("component"),
                parent=r.get("parent"),
                children=r.get("children", []),
                depth=r.get("depth", 0)
            )
            for r in component_relationships_raw
        ]

        dependency_graph = [
            DependencyNode(
                component=d.get("component"),
                imports_components=d.get("imports_components", []),
                imports_services=d.get("imports_services", []),
                imports_utilities=d.get("imports_utilities", []),
                imports_contexts=d.get("imports_contexts", []),
                imports_hooks=d.get("imports_hooks", []),
                imports_stores=d.get("imports_stores", []),
                imports_external_libraries=d.get("imports_external_libraries", [])
            )
            for d in dependency_graph_raw
        ]

        test_mapping = [
            TestMapping(
                component=t.get("component"),
                test_file=t.get("test_file"),
                testing_framework=t.get("testing_framework"),
                covered_features=t.get("covered_features", [])
            )
            for t in test_mapping_raw
        ]

        ir = FrameworkAgnosticIR(
            project_name=project_name,
            project_id=analysis_data.get("project_id"),
            pipeline_run_id=analysis_data.get("pipeline_run_id"),
            framework=analysis_data.get("framework", "React"),
            components=ir_components,
            elements=ir_elements,
            events=ir_events,
            state=ir_state,
            forms=ir_forms,
            services=ir_services,
            routes=ir_routes,
            dependencies=ir_dependencies,
            existing_tests=ir_tests,
            component_relationships=component_relationships,
            dependency_graph=dependency_graph,
            test_mapping=test_mapping
        )

        logger.info(
            "ReactIRMapper complete: %d components, %d elements, %d events, %d state entries mapped",
            len(ir.components),
            len(ir.elements),
            len(ir.events),
            len(ir.state),
        )
        return ir
