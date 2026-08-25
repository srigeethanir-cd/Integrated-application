"""
Component Analyzer for FCE.

Orchestrates all sub-extractors for a single component or custom hook data dict.
"""

from typing import Any, Dict, Optional
from app.services.frontend_context.api_analyzer import ApiAnalyzer
from app.services.frontend_context.behavior_mapper import BehaviorMapper
from app.services.frontend_context.condition_analyzer import ConditionAnalyzer
from app.services.frontend_context.dependency_analyzer import DependencyAnalyzer
from app.services.frontend_context.event_extractor import EventExtractor
from app.services.frontend_context.function_extractor import FunctionExtractor
from app.services.frontend_context.hook_extractor import HookExtractor
from app.services.frontend_context.models import SingleComponentFrontendContext
from app.services.frontend_context.props_extractor import PropsExtractor
from app.services.frontend_context.relationship_analyzer import RelationshipAnalyzer
from app.services.frontend_context.state_extractor import StateExtractor


class ComponentAnalyzer:
    """Combines all sub-extractors to build a SingleComponentFrontendContext."""

    def __init__(self) -> None:
        self._props_ext = PropsExtractor()
        self._state_ext = StateExtractor()
        self._hook_ext = HookExtractor()
        self._fn_ext = FunctionExtractor()
        self._event_ext = EventExtractor()
        self._cond_ext = ConditionAnalyzer()
        self._dep_ext = DependencyAnalyzer()
        self._api_ext = ApiAnalyzer()
        self._rel_ext = RelationshipAnalyzer()
        self._behavior_mapper = BehaviorMapper()

    def analyze_component(
        self,
        comp_data: Dict[str, Any],
        project_id: Optional[str] = None,
        pipeline_run_id: Optional[str] = None,
        framework: str = "React",
    ) -> SingleComponentFrontendContext:
        comp_name = comp_data.get("name") or comp_data.get("component_name") or "Component"
        comp_id = f"comp_{comp_name}"
        src_file = comp_data.get("file_path") or comp_data.get("source_file") or f"src/{comp_name}.jsx"

        props = self._props_ext.extract(comp_data)
        states = self._state_ext.extract(comp_data)
        hooks = self._hook_ext.extract(comp_data)
        fns = self._fn_ext.extract(comp_data)
        events = self._event_ext.extract(comp_data)
        conds = self._cond_ext.extract(comp_data)
        deps = self._dep_ext.extract(comp_data)
        api_calls = self._api_ext.extract(comp_data)
        children = self._rel_ext.extract(comp_data)

        # Map behaviors & state transitions
        behaviors = self._behavior_mapper.map_behaviors(comp_id, fns, events, states)
        transitions = self._behavior_mapper.map_state_transitions(fns, events, states)

        return SingleComponentFrontendContext(
            project_id=project_id,
            pipeline_run_id=pipeline_run_id,
            component_id=comp_id,
            component_name=comp_name,
            source_file=src_file,
            framework=framework,
            props=props,
            states=states,
            hooks=hooks,
            functions=fns,
            events=events,
            conditions=conds,
            api_calls=api_calls,
            validations=[],
            side_effects=[],
            child_components=children,
            dependencies=deps,
            behaviors=behaviors,
            state_transitions=transitions,
        )
