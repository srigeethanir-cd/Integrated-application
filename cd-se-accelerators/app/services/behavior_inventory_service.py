"""
Behavior Inventory Service – Deep Frontend Code Analysis & Inventory Builder.

Extracts a detailed Frontend Behavior Inventory from project analyzer AST results,
performing function-level behavior analysis, state transition identification,
and mandatory validation logging before downstream test generation.
"""

import logging
from typing import Any, Dict, List, Optional, Set, Union

from app.models.behavior_inventory_models import (
    ApiCallBehaviorItem,
    BehaviorInventoryResponse,
    ComponentBehaviorInventory,
    ConditionBehaviorItem,
    FunctionBehaviorItem,
    PropBehaviorItem,
    StateBehaviorItem,
    StateTransitionItem,
    ValidationBehaviorItem,
)

logger = logging.getLogger(__name__)


class BehaviorInventoryService:
    """Service that transforms raw parser outputs into a structured Frontend Behavior Inventory."""

    def build_inventory(
        self,
        analysis_result: Any,
        project_name: str = "Project",
        project_id: Optional[str] = None,
        pipeline_run_id: Optional[str] = None,
        framework: str = "React",
    ) -> BehaviorInventoryResponse:
        """Build a complete Frontend Behavior Inventory from analysis result data.

        Args:
            analysis_result: AnalyzerResponse, ReactAnalysisResult, AngularAnalysisResult or dict.
            project_name: Name of the analyzed project.
            project_id: Unique project identifier.
            pipeline_run_id: Unique pipeline run identifier.
            framework: Detected framework name (React, Next.js, Angular).

        Returns:
            A typed BehaviorInventoryResponse containing detailed component inventories.
        """
        logger.info("BehaviorInventoryService: Building Frontend Behavior Inventory for framework='%s'", framework)

        # Normalize analysis result to dict/object list
        components_raw = self._extract_raw_components(analysis_result)

        inventories: List[ComponentBehaviorInventory] = []

        total_functions = 0
        total_states = 0
        total_hooks = 0
        total_handlers = 0
        total_api_calls = 0
        total_validations = 0

        for comp_data in components_raw:
            inventory_item = self._process_single_component(comp_data)
            inventories.append(inventory_item)

            total_functions += len(inventory_item.functions)
            total_states += len(inventory_item.states)
            total_hooks += len(inventory_item.hooks)
            total_handlers += len(inventory_item.event_handlers)
            total_api_calls += len(inventory_item.api_calls)
            total_validations += len(inventory_item.validations)

        response = BehaviorInventoryResponse(
            project_name=project_name,
            project_id=project_id,
            pipeline_run_id=pipeline_run_id,
            framework=framework,
            total_components=len(inventories),
            total_functions=total_functions,
            total_states=total_states,
            total_hooks=total_hooks,
            total_handlers=total_handlers,
            total_api_calls=total_api_calls,
            total_validations=total_validations,
            inventory=inventories,
        )

        # MANDATORY INTERMEDIATE VALIDATION LOGGING (Requirement 9)
        logger.info("==================================================")
        logger.info("FRONTEND BEHAVIOR INVENTORY VALIDATION LOG")
        logger.info("Components discovered: %d", response.total_components)
        logger.info("Functions discovered: %d", response.total_functions)
        logger.info("States discovered: %d", response.total_states)
        logger.info("Hooks discovered: %d", response.total_hooks)
        logger.info("Handlers discovered: %d", response.total_handlers)
        logger.info("API calls discovered: %d", response.total_api_calls)
        logger.info("Validations discovered: %d", response.total_validations)
        logger.info("==================================================")

        return response

    # ------------------------------------------------------------------
    # Private Helpers – Extraction & Synthesis
    # ------------------------------------------------------------------

    def _extract_raw_components(self, analysis_result: Any) -> List[Dict[str, Any]]:
        """Safely extract list of raw component data dicts from various analysis result formats."""
        if not analysis_result:
            return []

        if isinstance(analysis_result, dict):
            # Might be AnalyzerResponse dict wrapper or direct result dict
            if "analysis" in analysis_result and isinstance(analysis_result["analysis"], dict):
                return analysis_result["analysis"].get("components", [])
            return analysis_result.get("components", [])

        # Pydantic model object
        if hasattr(analysis_result, "analysis") and analysis_result.analysis:
            analysis_obj = analysis_result.analysis
            if hasattr(analysis_obj, "components"):
                return [c.model_dump() if hasattr(c, "model_dump") else dict(c) for c in analysis_obj.components]
            if isinstance(analysis_obj, dict):
                return analysis_obj.get("components", [])

        if hasattr(analysis_result, "components"):
            comps = analysis_result.components
            return [c.model_dump() if hasattr(c, "model_dump") else dict(c) for c in comps]

        return []

    def _process_single_component(self, comp_data: Dict[str, Any]) -> ComponentBehaviorInventory:
        """Process raw AST dictionary for one component/hook into ComponentBehaviorInventory."""
        comp_name = comp_data.get("name", "UnknownComponent")
        source_file = comp_data.get("file_path") or comp_data.get("source_file") or f"src/components/{comp_name}.jsx"

        # Determine component type
        comp_type = "component"
        if comp_name.startswith("use") and len(comp_name) > 3 and comp_name[3].isupper():
            comp_type = "hook"
        elif "Service" in comp_name or "service" in source_file.lower():
            comp_type = "service"

        # 1. State Extraction
        states_list: List[StateBehaviorItem] = []
        state_names: List[str] = []
        state_setter_map: Dict[str, str] = {}  # state_name -> setter_name

        raw_states = comp_data.get("state") or comp_data.get("states") or []
        for st in raw_states:
            st_dict = st if isinstance(st, dict) else (st.model_dump() if hasattr(st, "model_dump") else {})
            s_name = st_dict.get("name", "")
            if not s_name:
                continue

            init_val = str(st_dict.get("initial_value", '""')) if st_dict.get("initial_value") is not None else '""'
            s_type = st_dict.get("state_type") or st_dict.get("type") or "unknown"
            setter_name = st_dict.get("setter_name") or f"set{s_name[0].upper() + s_name[1:]}"

            states_list.append(
                StateBehaviorItem(
                    name=s_name,
                    initial_value=init_val,
                    type=s_type,
                    setter_name=setter_name,
                )
            )
            state_names.append(s_name)
            state_setter_map[s_name] = setter_name

        # 2. Hooks Extraction
        hooks_list: List[str] = []
        raw_hooks = comp_data.get("hooks") or []
        for hk in raw_hooks:
            hk_name = hk.get("name") if isinstance(hk, dict) else str(hk)
            if hk_name and hk_name not in hooks_list:
                hooks_list.append(hk_name)

        if not hooks_list and states_list:
            hooks_list.append("useState")

        # 3. Props / Inputs Extraction
        props_list: List[PropBehaviorItem] = []
        raw_props = comp_data.get("props") or comp_data.get("inputs") or []
        for pr in raw_props:
            pr_dict = pr if isinstance(pr, dict) else (pr.model_dump() if hasattr(pr, "model_dump") else {})
            p_name = pr_dict.get("name")
            if p_name:
                props_list.append(
                    PropBehaviorItem(
                        name=p_name,
                        type=pr_dict.get("type", "any"),
                        default_value=pr_dict.get("default_value"),
                        required=pr_dict.get("required", False),
                    )
                )

        # 4. Functions & Handlers Analysis
        functions_list: List[FunctionBehaviorItem] = []
        event_handlers_list: List[str] = []
        state_transitions_list: List[StateTransitionItem] = []

        raw_functions = comp_data.get("functions") or []
        raw_handlers = comp_data.get("event_handlers") or comp_data.get("handlers") or []

        # Combine all function entries cleanly
        seen_fn_names: Set[str] = set()

        # Process event handlers
        for eh in raw_handlers:
            eh_dict = eh if isinstance(eh, dict) else (eh.model_dump() if hasattr(eh, "model_dump") else {})
            fn_name = eh_dict.get("name") or eh_dict.get("handler_name") or eh_dict.get("function")
            if not fn_name:
                continue

            event_handlers_list.append(fn_name)
            seen_fn_names.add(fn_name)

            # Analyze function state modifications & side effects
            updates_state = eh_dict.get("updates_state") or []
            if not updates_state and states_list:
                # Infer modified state from function name (e.g. handleEmailChange -> email)
                for s_item in states_list:
                    if s_item.name.lower() in fn_name.lower():
                        updates_state.append(s_item.name)

            not_modified = [s for s in state_names if s not in updates_state]

            # Infer event type consumed
            event_type = eh_dict.get("event") or "event"
            if "click" in fn_name.lower() or "button" in fn_name.lower():
                event_type = "click"
            elif "change" in fn_name.lower() or "input" in fn_name.lower():
                event_type = "change"
            elif "submit" in fn_name.lower() or "form" in fn_name.lower():
                event_type = "submit"

            side_effects = []
            if eh_dict.get("prevent_default"):
                side_effects.append("event.preventDefault()")
            if eh_dict.get("stop_propagation"):
                side_effects.append("event.stopPropagation()")
            if eh_dict.get("navigation"):
                side_effects.append("navigation / route change")
            if eh_dict.get("service_calls"):
                side_effects.extend([f"service call: {s}" for s in eh_dict.get("service_calls")])

            # Formulate explicit behavior string
            behavior_desc = f"handles {event_type} event"
            if updates_state:
                behavior_desc = f"updates {', '.join(updates_state)} state from {event_type} event"
            if "prevent_default" in str(side_effects):
                behavior_desc = "prevents default form submission and " + behavior_desc

            functions_list.append(
                FunctionBehaviorItem(
                    name=fn_name,
                    behavior=behavior_desc,
                    inputs=["event"] if event_type != "event" else [],
                    outputs="void",
                    state_modified=updates_state,
                    state_not_modified=not_modified,
                    events_consumed=[event_type] if event_type != "event" else [],
                    conditions=[],
                    side_effects=side_effects,
                    dependencies=eh_dict.get("service_calls", []),
                    success_path=f"Executes {fn_name} successfully and applies state/DOM updates",
                    failure_path=f"Fails if event target is missing or invalid",
                )
            )

            # Build state transitions for modified states
            for s_mod in updates_state:
                s_obj = next((s for s in states_list if s.name == s_mod), None)
                init_val = s_obj.initial_value if s_obj else '""'
                setter = s_obj.setter_name if s_obj else f"set{s_mod[0].upper() + s_mod[1:]}"

                sample_val = '"user@test.com"' if 'email' in s_mod.lower() else ('true' if 'remember' in s_mod.lower() or 'check' in s_mod.lower() else '"new_value"')

                state_transitions_list.append(
                    StateTransitionItem(
                        initial_state=f"{s_mod} = {init_val}",
                        triggering_function=f"{fn_name}({sample_val})",
                        state_transition=f"{setter}({sample_val})",
                        resulting_state=f"{s_mod} = {sample_val}",
                    )
                )

        # Process general functions
        for fn in raw_functions:
            fn_dict = fn if isinstance(fn, dict) else (fn.model_dump() if hasattr(fn, "model_dump") else {})
            fn_name = fn_dict.get("name")
            if not fn_name or fn_name in seen_fn_names:
                continue

            seen_fn_names.add(fn_name)
            params = fn_dict.get("params") or fn_dict.get("parameters") or []

            # Infer state modifications
            modified = [s for s in state_names if s.lower() in fn_name.lower()]
            not_modified = [s for s in state_names if s not in modified]

            behavior_desc = fn_dict.get("description") or f"executes {fn_name} functionality"
            if modified:
                behavior_desc = f"modifies {', '.join(modified)} state"

            functions_list.append(
                FunctionBehaviorItem(
                    name=fn_name,
                    behavior=behavior_desc,
                    inputs=params,
                    outputs=fn_dict.get("return_type", "void"),
                    state_modified=modified,
                    state_not_modified=not_modified,
                    events_consumed=[],
                    conditions=[],
                    side_effects=[],
                    dependencies=[],
                    success_path=f"{fn_name} completes cleanly",
                    failure_path=f"{fn_name} throws or returns fallback on error",
                )
            )

        # 5. API Calls Extraction
        api_calls_list: List[ApiCallBehaviorItem] = []
        raw_api = comp_data.get("api_calls") or []
        for api in raw_api:
            api_dict = api if isinstance(api, dict) else (api.model_dump() if hasattr(api, "model_dump") else {})
            ep = api_dict.get("endpoint") or api_dict.get("url") or "api/endpoint"
            method = api_dict.get("http_method") or "GET"
            api_calls_list.append(
                ApiCallBehaviorItem(
                    endpoint=ep,
                    http_method=method,
                    is_async=bool(api_dict.get("is_async", True)),
                    has_error_handling=bool(api_dict.get("has_error_handling", False)),
                    in_use_effect=bool(api_dict.get("in_use_effect", False)),
                )
            )

        # 6. Validations Extraction
        validations_list: List[ValidationBehaviorItem] = []
        raw_val = comp_data.get("validations") or comp_data.get("forms") or []
        for v in raw_val:
            if isinstance(v, dict):
                f_name = v.get("field") or v.get("form_name") or "formField"
                rule_desc = v.get("rule") or "required field validation"
                validations_list.append(
                    ValidationBehaviorItem(
                        field=f_name,
                        rule=rule_desc,
                        error_message=v.get("error_message") or f"{f_name} is required",
                        condition=v.get("condition"),
                    )
                )

        # 7. Conditions Extraction
        conditions_list: List[ConditionBehaviorItem] = []
        raw_cond = comp_data.get("conditions") or comp_data.get("conditional_renders") or []
        for c in raw_cond:
            if isinstance(c, dict):
                expr = c.get("expression") or c.get("condition")
                if expr:
                    conditions_list.append(
                        ConditionBehaviorItem(
                            expression=expr,
                            true_branch=c.get("true_branch"),
                            false_branch=c.get("false_branch"),
                        )
                    )

        return ComponentBehaviorInventory(
            component=comp_name,
            source_file=source_file,
            component_type=comp_type,
            states=states_list,
            functions=functions_list,
            hooks=hooks_list,
            props=props_list,
            event_handlers=event_handlers_list,
            validations=validations_list,
            api_calls=api_calls_list,
            conditions=conditions_list,
            state_transitions=state_transitions_list,
        )
