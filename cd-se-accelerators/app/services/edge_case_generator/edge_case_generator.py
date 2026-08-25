"""
Edge Case Generator Service – Module 6.

Orchestrates the conversion of test strategies from Module 5 into mapped,
framework-agnostic edge case scenarios.
Uses EdgeCaseRegistry to select and execute generators, deduplicates scenarios,
performs validation, and returns the EdgeCasePlanResponse.
"""

import logging
from typing import Any, Dict, List, Set, Union
from app.models.strategy_models import StrategyPlanResponse
from app.models.edge_case_models import EdgeCasePlanRequest, EdgeCasePlanResponse, EdgeCaseScenario
from app.services.edge_case_generator.generators import (
    AccessibilityEdgeCaseGenerator,
    EventEdgeCaseGenerator,
    FormEdgeCaseGenerator,
    RouteEdgeCaseGenerator,
    ServiceEdgeCaseGenerator,
    StateEdgeCaseGenerator,
    PropEdgeCaseGenerator,
    RenderingEdgeCaseGenerator,
)
from app.services.edge_case_generator.edge_case_registry import EdgeCaseRegistry

logger = logging.getLogger(__name__)


def _build_default_edge_case_registry() -> EdgeCaseRegistry:
    """Populate default edge case generators."""
    registry = EdgeCaseRegistry()
    registry.register(FormEdgeCaseGenerator())
    registry.register(EventEdgeCaseGenerator())
    registry.register(StateEdgeCaseGenerator())
    registry.register(ServiceEdgeCaseGenerator())
    registry.register(RouteEdgeCaseGenerator())
    registry.register(AccessibilityEdgeCaseGenerator())
    registry.register(PropEdgeCaseGenerator())
    registry.register(RenderingEdgeCaseGenerator())
    return registry


class EdgeCaseGeneratorService:
    """Main Edge Case Generator Service for Module 6."""

    def __init__(self, registry: EdgeCaseRegistry | None = None) -> None:
        self._registry = registry or _build_default_edge_case_registry()
        logger.info(
            "EdgeCaseGeneratorService initialised with %d generator(s)",
            len(self._registry.get_generators()),
        )

    def generate_edge_cases(
        self, strategy_plan: Union[EdgeCasePlanRequest, StrategyPlanResponse, Dict[str, Any]]
    ) -> EdgeCasePlanResponse:
        """Inspect Strategy plan and optional IR, map to generators, compile, deduplicate and validate edge cases.

        Args:
            strategy_plan: EdgeCasePlanRequest, StrategyPlanResponse model, or raw dictionary.

        Returns:
            EdgeCasePlanResponse object containing mapped edge case scenarios.

        Raises:
            ValueError: If validation fails.
        """
        logger.info("EdgeCaseGeneratorService: Starting edge case generation")

        # Normalize input
        if isinstance(strategy_plan, EdgeCasePlanRequest):
            if strategy_plan.ir:
                from app.utils.ir_cache import cache_ir
                cache_ir(strategy_plan.ir)
            data_dict = strategy_plan.strategy_plan.model_dump()
        elif isinstance(strategy_plan, StrategyPlanResponse):
            data_dict = strategy_plan.model_dump()
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
                data_dict = strategy_plan["strategy_plan"]
            else:
                data_dict = strategy_plan
        else:
            raise ValueError("Input must be an EdgeCasePlanRequest, StrategyPlanResponse, or dict.")

        project_name = data_dict.get("project_name", "IngestedProject")
        project_id = data_dict.get("project_id")
        pipeline_run_id = data_dict.get("pipeline_run_id")
        framework = data_dict.get("framework", "Unknown")
        strategies_raw = data_dict.get("strategies", [])

        compiled_scenarios: List[EdgeCaseScenario] = []

        # Convert raw dictionaries to TestStrategy models internally for safe attribute access
        from app.models.strategy_models import TestStrategy
        strategies: List[TestStrategy] = []
        for s_dict in strategies_raw:
            try:
                st_model = TestStrategy.model_validate(s_dict)
                if not st_model.project_id and project_id:
                    st_model.project_id = project_id
                if not st_model.pipeline_run_id and pipeline_run_id:
                    st_model.pipeline_run_id = pipeline_run_id
                strategies.append(st_model)
            except Exception as exc:
                logger.error("Failed to validate input strategy dict: %s", exc)
                raise ValueError(f"Invalid strategy payload input: {exc}") from exc

        # Execute generators
        for generator in self._registry.get_generators():
            logger.info("Running Edge Case generator: %s", generator.category_name)
            for strat in strategies:
                if generator.supports(strat):
                    try:
                        scenarios = generator.generate(strat)
                        for sc in scenarios:
                            sc.project_id = strat.project_id or project_id
                            sc.pipeline_run_id = strat.pipeline_run_id or pipeline_run_id
                            sc.source_file = strat.source_file
                        compiled_scenarios.extend(scenarios)
                    except Exception as exc:
                        logger.error(
                            "Error in generator '%s' for strategy '%s': %s",
                            generator.category_name,
                            strat.id,
                            exc,
                        )
                        raise ValueError(f"Edge case mapping failed in '{generator.category_name}': {exc}") from exc

        # Enrich scenarios with behavioral explanations derived from IR
        from app.utils.ir_cache import get_cached_ir
        cached_ir = get_cached_ir(pipeline_run_id or project_id or project_name)

        for sc in compiled_scenarios:
            sc.project_id = sc.project_id or project_id
            sc.pipeline_run_id = sc.pipeline_run_id or pipeline_run_id
            strat = next((s for s in strategies if s.id == sc.strategy_id), None)
            if strat:
                if strat.source_file and not sc.source_file:
                    sc.source_file = strat.source_file
                if getattr(strat, "target_function", None) and not getattr(sc, "target_function", None):
                    sc.target_function = strat.target_function
            comp_name = sc.component_id.removeprefix("comp_") if sc.component_id else (strat.target_component if strat else "Component")
            comp = next((c for c in cached_ir.components if c.name == comp_name or c.id == sc.component_id), None) if cached_ir else None

            # Generate why_it_exists
            if "rapid" in sc.id.lower() or "double" in sc.id.lower() or "toggle" in sc.id.lower():
                sc.why_it_exists = f"Component '{comp_name}' registers interactive event handlers and reactive state transitions."
                sc.what_behavior_it_validates = f"Validates that consecutive user interactions maintain deterministic state synchronization in {comp_name}."
                sc.what_failure_it_prevents = f"Prevents race conditions, state tearing, and duplicate handler invocations."
            elif "unmount" in sc.id.lower() or "async" in sc.id.lower():
                sc.why_it_exists = f"Component '{comp_name}' contains asynchronous callbacks or side effects."
                sc.what_behavior_it_validates = f"Validates clean teardown and cancellation of async operations upon unmount."
                sc.what_failure_it_prevents = f"Prevents memory leaks, unhandled promise rejections, and state updates on unmounted component."
            elif "null" in sc.id.lower() or "undefined" in sc.id.lower() or "prop" in sc.id.lower():
                sc.why_it_exists = f"Component '{comp_name}' accepts external prop inputs."
                sc.what_behavior_it_validates = f"Validates graceful fallback or rendering default values when props are missing/invalid."
                sc.what_failure_it_prevents = f"Prevents uncaught TypeError crashes during render phase."
            elif "empty" in sc.id.lower() or "dataset" in sc.id.lower() or "array" in sc.id.lower():
                sc.why_it_exists = f"Component '{comp_name}' renders collection or array items."
                sc.what_behavior_it_validates = f"Validates empty state messaging and virtualized layout stability under high volume."
                sc.what_failure_it_prevents = f"Prevents indexing out-of-bounds errors and rendering freezes."
            elif "keyboard" in sc.id.lower() or "focus" in sc.id.lower() or "a11y" in sc.id.lower():
                sc.why_it_exists = f"Component '{comp_name}' includes accessible interactive elements requiring keyboard navigation."
                sc.what_behavior_it_validates = f"Validates Tab index focus management and keypress activation."
                sc.what_failure_it_prevents = f"Prevents keyboard lockouts and accessibility compliance violations."
            elif "strictmode" in sc.id.lower() or "loop" in sc.id.lower() or "rerender" in sc.id.lower():
                sc.why_it_exists = f"Component '{comp_name}' manages local hooks and effect dependencies."
                sc.what_behavior_it_validates = f"Validates idempotent effect invocation under React StrictMode double rendering."
                sc.what_failure_it_prevents = f"Prevents infinite re-render loops and duplicated side effect execution."
            else:
                sc.why_it_exists = f"Component '{comp_name}' exhibits state and event behavior."
                sc.what_behavior_it_validates = sc.expected_behavior or sc.description
                sc.what_failure_it_prevents = f"Prevents unexpected UI state regressions in {comp_name}."

        # Deduplicate
        unique_scenarios = self._deduplicate_scenarios(compiled_scenarios)

        # Validate
        self.validate_edge_cases(unique_scenarios, strategies)

        # Deterministic sorting: priority (High -> Medium -> Low), then category, then ID
        priority_order = {"High": 0, "Medium": 1, "Low": 2}
        unique_scenarios.sort(key=lambda s: (priority_order.get(s.priority, 9), s.category, s.id))

        logger.info(
            "EdgeCaseGeneratorService: Completed for '%s' – Total Edge Cases generated: %d",
            project_name,
            len(unique_scenarios),
        )

        return EdgeCasePlanResponse(
            project_name=project_name,
            project_id=project_id,
            pipeline_run_id=pipeline_run_id,
            framework=framework,
            total_edge_cases=len(unique_scenarios),
            edge_cases=unique_scenarios,
        )

    def _deduplicate_scenarios(self, scenarios: List[EdgeCaseScenario]) -> List[EdgeCaseScenario]:
        """Remove duplicate edge case scenarios based on strategy_id + component_id + edge_case_type."""
        seen_keys: Set[str] = set()
        unique: List[EdgeCaseScenario] = []
        duplicates_count = 0

        for sc in scenarios:
            composite_key = f"{sc.strategy_id}:{sc.component_id}:{sc.edge_case_type}"
            if composite_key in seen_keys:
                duplicates_count += 1
                logger.debug("Removing duplicate edge case: id='%s', key='%s'", sc.id, composite_key)
            else:
                seen_keys.add(composite_key)
                unique.append(sc)

        if duplicates_count > 0:
            logger.info("Duplicate edge case removal: removed %d duplicate(s)", duplicates_count)

        return unique

    def validate_edge_cases(
        self, scenarios: List[EdgeCaseScenario], strategies: List[Any]
    ) -> None:
        """Validate generated edge cases for correctness."""
        logger.info("EdgeCaseGeneratorService: Validating %d edge case(s)", len(scenarios))

        valid_priorities = {"high", "medium", "low"}
        valid_categories = {"Forms", "Events", "State", "Services", "Routing", "Accessibility"}
        known_strategy_ids = set(s.id for s in strategies)

        seen_ids = set()

        for sc in scenarios:
            # 1. Duplicate ID Check
            if sc.id in seen_ids:
                msg = f"Validation Error: Duplicate Edge Case ID found: {sc.id}"
                logger.error(msg)
                raise ValueError(msg)
            seen_ids.add(sc.id)

            # 2. Missing Strategy Reference Check
            if sc.strategy_id not in known_strategy_ids:
                msg = f"Validation Error: Edge case '{sc.id}' references unknown strategy ID '{sc.strategy_id}'."
                logger.error(msg)
                raise ValueError(msg)

            # 3. Invalid Priorities Check
            if sc.priority.lower() not in valid_priorities:
                msg = f"Validation Error: Edge case '{sc.id}' has invalid priority level '{sc.priority}'."
                logger.error(msg)
                raise ValueError(msg)

            # 4. Invalid Categories Check
            if sc.category not in valid_categories:
                msg = f"Validation Error: Edge case '{sc.id}' has invalid category label '{sc.category}'."
                logger.error(msg)
                raise ValueError(msg)

        logger.info("EdgeCaseGeneratorService: Validation passed successfully.")
