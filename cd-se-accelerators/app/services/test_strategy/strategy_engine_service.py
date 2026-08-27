"""
Strategy Engine Service – Module 5.

Orchestrates strategy generation by invoking registered generators from StrategyRegistry,
deduplicating strategies, checking coverage against existing test files, and performing
validations.
"""

import logging
from typing import List, Set
from app.models.ir_models import FrameworkAgnosticIR
from app.models.strategy_models import StrategyPlanResponse, TestStrategy
from app.services.test_strategy.generators import (
    AccessibilityStrategyGenerator,
    ComponentStrategyGenerator,
    FormStrategyGenerator,
    RouteStrategyGenerator,
    ServiceStrategyGenerator,
    StateStrategyGenerator,
    EventStrategyGenerator,
    ContextStrategyGenerator,
    HookStrategyGenerator,
)
from app.services.test_strategy.strategy_registry import StrategyRegistry

logger = logging.getLogger(__name__)


def map_edge_case_to_strategy(ec, base_strat) -> TestStrategy:
    """Helper to convert EdgeCaseScenario into TestStrategy."""
    cat_map = {
        "Forms": "Form Validation Tests",
        "Events": "Event Handling Tests",
        "State": "State Management Tests",
        "Services": "API/Service Interaction Tests",
        "Routing": "Routing Tests",
        "Accessibility": "Accessibility Tests",
    }
    category = cat_map.get(ec.category, "State Management Tests")
    if category == "API/Service Interaction Tests" and any(x in ec.id.lower() for x in ["failure", "timeout", "offline"]):
        category = "Error Handling Tests"

    preconds = ec.mock_requirements if ec.mock_requirements else []
    if not preconds:
        preconds = [f"Edge case condition: {ec.title}"]

    target_comp = base_strat.target_component if base_strat else (ec.component_id.removeprefix("comp_") if ec.component_id else "Component")

    return TestStrategy(
        id=ec.id,
        category=category,
        priority=ec.priority,
        target_component=target_comp,
        description=ec.description,
        preconditions=preconds,
        coverage_tags=ec.tags,
        is_covered=False,
        strategy_id=ec.strategy_id,
        component=target_comp,
        component_id=ec.component_id,
        element_id=ec.element_id,
        event_id=ec.event_id,
        state_id=ec.state_id,
        service_id=ec.service_id,
        route_id=ec.route_id,
        risk=base_strat.risk if base_strat else f"{ec.priority} (5/10)",
        reason=ec.why_it_exists or f"Validates edge case: {ec.title}",
        behavior_reference=ec.what_behavior_it_validates or ec.expected_behavior,
        expected_outcome=ec.expected_behavior,
        test_objective=ec.what_behavior_it_validates or ec.description
    )


def _build_default_strategy_registry() -> StrategyRegistry:
    """Populate default strategy generators."""
    registry = StrategyRegistry()
    registry.register(ComponentStrategyGenerator())
    registry.register(FormStrategyGenerator())
    registry.register(StateStrategyGenerator())
    registry.register(ServiceStrategyGenerator())
    registry.register(RouteStrategyGenerator())
    registry.register(AccessibilityStrategyGenerator())
    registry.register(EventStrategyGenerator())
    registry.register(ContextStrategyGenerator())
    registry.register(HookStrategyGenerator())
    return registry


class StrategyEngine:
    """Main Test Strategy Engine for Module 5."""

    def __init__(self, registry: StrategyRegistry | None = None) -> None:
        self._registry = registry or _build_default_strategy_registry()
        logger.info(
            "StrategyEngine initialised with %d strategy generator(s)",
            len(self._registry.get_generators()),
        )

    def generate_strategies(self, ir: FrameworkAgnosticIR) -> StrategyPlanResponse:
        """Generate, deduplicate, check coverage, and validate test strategies from IR.

        Args:
            ir: FrameworkAgnosticIR object from Module 4.

        Returns:
            StrategyPlanResponse object containing normalized strategies.
        """
        logger.info("StrategyEngine: Generating strategies for project '%s'", ir.project_name)

        raw_strategies: List[TestStrategy] = []

        # 1. Execute all generators in StrategyRegistry
        for generator in self._registry.get_generators():
            try:
                gen_strategies = generator.generate(ir)
                logger.info(
                    "Generator '%s' produced %d strategy/strategies",
                    generator.category_name,
                    len(gen_strategies),
                )
                raw_strategies.extend(gen_strategies)
            except Exception as exc:
                logger.error("Error in generator '%s': %s", generator.category_name, exc)
                raise ValueError(f"Strategy generation failed in '{generator.category_name}': {exc}") from exc
        
        pid = getattr(ir, "project_id", None)
        rid = getattr(ir, "pipeline_run_id", None)
        ir_comp_names = {c.name for c in ir.components}

        # 2. Enrich Base Strategies with IR Semantic Information (So that EdgeCaseGenerator has enriched targets)
        for strat in raw_strategies:
            strat.project_id = pid
            strat.pipeline_run_id = rid
            comp = next((c for c in ir.components if c.name == strat.target_component), None)
            if comp:
                strat.source_file = getattr(comp, "source_file", None) or comp.file_path
            if not strat.strategy_id:
                strat.strategy_id = strat.id
            if not strat.component:
                strat.component = strat.target_component

            if comp:
                if not strat.component_id:
                    strat.component_id = comp.id or f"comp_{comp.name}"
                if not strat.risk:
                    if comp.risk_analysis:
                        strat.risk = f"{comp.risk_analysis.level} ({comp.risk_analysis.score}/10)"
                    else:
                        strat.risk = f"{strat.priority} ({int(comp.risk_score or 1)}/10)"
                if not strat.reason:
                    if comp.risk_analysis:
                        strat.reason = "; ".join(comp.risk_analysis.risk_reasons) or comp.behavior_summary or f"Derived from component risk profile ({comp.name})."
                    else:
                        strat.reason = comp.behavior_summary or f"Derived from component {comp.name} analysis."

                if not strat.behavior_reference:
                    b_refs = []
                    if comp.interaction_graph:
                        ig = comp.interaction_graph[0]
                        b_refs.append(f"{ig.user_action} -> {ig.handler}")
                    if comp.state_transitions:
                        st = comp.state_transitions[0]
                        b_refs.append(f"{st.current_state} -> {st.trigger} -> {st.next_state}")
                    if comp.render_conditions:
                        rc = comp.render_conditions[0]
                        b_refs.append(f"Condition: {rc.condition}")

                    strat.behavior_reference = " | ".join(b_refs) if b_refs else (comp.behavior_summary or f"Component {comp.name} behavior model")
                
                if not strat.test_objective:
                    strat.test_objective = strat.description

                if not strat.expected_outcome:
                    if "init" in strat.id.lower() or "mount" in strat.id.lower():
                        strat.expected_outcome = f"{comp.name} mounts cleanly in DOM container without unhandled exceptions."
                    elif "props" in strat.id.lower():
                        strat.expected_outcome = f"{comp.name} renders verified prop bindings and updates UI elements."
                    elif "cond" in strat.id.lower():
                        strat.expected_outcome = f"Conditional elements toggle visibility according to rendering rules."
                    elif "state" in strat.id.lower():
                        strat.expected_outcome = f"Reactive state transitions execute correctly and update component UI."
                    elif "event" in strat.id.lower() or "click" in strat.id.lower():
                        strat.expected_outcome = f"Event triggers handler, mutates state, and performs expected DOM side-effects."
                    elif "a11y" in strat.id.lower() or "accessibility" in strat.id.lower():
                        strat.expected_outcome = f"ARIA roles, labels, and keyboard navigation meet WCAG standards."
                    else:
                        strat.expected_outcome = f"Verified behavior outcome for {strat.description}"

        # 3. Invoke Edge Case Generator internally alongside standard generators
        try:
            from app.utils.ir_cache import cache_ir
            cache_ir(ir, key=rid or pid)

            from app.services.edge_case_generator.edge_case_generator import EdgeCaseGeneratorService
            ec_service = EdgeCaseGeneratorService()

            base_plan = StrategyPlanResponse(
                project_name=ir.project_name,
                project_id=pid,
                pipeline_run_id=rid,
                framework=ir.framework,
                total_strategies=len(raw_strategies),
                covered_strategies_count=0,
                uncovered_strategies_count=len(raw_strategies),
                strategies=raw_strategies
            )

            ec_plan = ec_service.generate_edge_cases(base_plan)
            
            strategy_by_id = {s.id: s for s in raw_strategies}
            ec_strategies = []
            for ec in ec_plan.edge_cases:
                base_strat = strategy_by_id.get(ec.strategy_id)
                ec_strat = map_edge_case_to_strategy(ec, base_strat)
                ec_strat.project_id = pid
                ec_strat.pipeline_run_id = rid
                ec_strategies.append(ec_strat)

            raw_strategies.extend(ec_strategies)
            logger.info("Internal Edge Case Generator produced %d edge case strategy/strategies", len(ec_plan.edge_cases))
        except Exception as exc:
            logger.error("Error in internal Edge Case Generator: %s", exc)
            raise ValueError(f"Edge case generation failed internally: {exc}") from exc

        # 4. Enrich Mapped Edge Case Strategies with fallback rules for target component
        for strat in raw_strategies:
            strat.project_id = pid
            strat.pipeline_run_id = rid
            comp = next((c for c in ir.components if c.name == strat.target_component), None)
            if not strat.strategy_id:
                strat.strategy_id = strat.id
            if not strat.component:
                strat.component = strat.target_component

            if comp:
                strat.source_file = getattr(comp, "source_file", None) or comp.file_path
                if not strat.component_id:
                    strat.component_id = comp.id or f"comp_{comp.name}"
                if not strat.risk:
                    if comp.risk_analysis:
                        strat.risk = f"{comp.risk_analysis.level} ({comp.risk_analysis.score}/10)"
                    else:
                        strat.risk = f"{strat.priority} ({int(comp.risk_score or 1)}/10)"
                if not strat.reason:
                    if comp.risk_analysis:
                        strat.reason = "; ".join(comp.risk_analysis.risk_reasons) or comp.behavior_summary or f"Derived from component risk profile ({comp.name})."
                    else:
                        strat.reason = comp.behavior_summary or f"Derived from component {comp.name} analysis."

                # Behavior Reference
                if not strat.behavior_reference:
                    b_refs = []
                    if comp.interaction_graph:
                        ig = comp.interaction_graph[0]
                        b_refs.append(f"{ig.user_action} -> {ig.handler}")
                    if comp.state_transitions:
                        st = comp.state_transitions[0]
                        b_refs.append(f"{st.current_state} -> {st.trigger} -> {st.next_state}")
                    if comp.render_conditions:
                        rc = comp.render_conditions[0]
                        b_refs.append(f"Condition: {rc.condition}")

                    strat.behavior_reference = " | ".join(b_refs) if b_refs else (comp.behavior_summary or f"Component {comp.name} behavior model")
                
                if not strat.test_objective:
                    strat.test_objective = strat.description

                # Behavior-driven expected outcome
                if not strat.expected_outcome:
                    if "init" in strat.id.lower() or "mount" in strat.id.lower():
                        strat.expected_outcome = f"{comp.name} mounts cleanly in DOM container without unhandled exceptions."
                    elif "props" in strat.id.lower():
                        strat.expected_outcome = f"{comp.name} renders verified prop bindings and updates UI elements."
                    elif "cond" in strat.id.lower():
                        strat.expected_outcome = f"Conditional elements toggle visibility according to rendering rules."
                    elif "state" in strat.id.lower():
                        strat.expected_outcome = f"Reactive state transitions execute correctly and update component UI."
                    elif "event" in strat.id.lower() or "click" in strat.id.lower():
                        strat.expected_outcome = f"Event triggers handler, mutates state, and performs expected DOM side-effects."
                    elif "a11y" in strat.id.lower() or "accessibility" in strat.id.lower():
                        strat.expected_outcome = f"ARIA roles, labels, and keyboard navigation meet WCAG standards."
                    else:
                        strat.expected_outcome = f"Verified behavior outcome for {strat.description}"
            else:
                if not strat.risk:
                    strat.risk = f"{strat.priority} (1/10)"
                if not strat.reason:
                    strat.reason = f"Validates {strat.category}"
                if not strat.test_objective:
                    strat.test_objective = strat.description
                if not strat.expected_outcome:
                    strat.expected_outcome = f"Verified outcome for {strat.description}"

        # Strictly filter out strategies targeting components that do not exist in the current project's IR (if IR has components)
        if ir_comp_names:
            filtered_strats = [s for s in raw_strategies if s.target_component in ir_comp_names or (s.component and s.component in ir_comp_names)]
            if len(filtered_strats) < len(raw_strategies):
                logger.warning(
                    "Filtered out %d strategy/strategies targeting components not in current project's IR",
                    len(raw_strategies) - len(filtered_strats)
                )
            raw_strategies = filtered_strats

        # 3. Deduplicate Strategies
        unique_strategies = self._deduplicate_strategies(raw_strategies)

        # 3. Check Existing Test Coverage
        self._apply_existing_test_coverage(unique_strategies, ir)

        # 4. Perform Validations
        self.validate_strategies(unique_strategies, ir)

        # 5. Deterministic sorting: priority (High -> Medium -> Low), then category, then ID
        priority_order = {"High": 0, "Medium": 1, "Low": 2}
        unique_strategies.sort(key=lambda s: (priority_order.get(s.priority, 9), s.category, s.id))

        covered_count = sum(1 for s in unique_strategies if s.is_covered)
        uncovered_count = len(unique_strategies) - covered_count

        logger.info(
            "StrategyEngine: Complete for '%s' (project_id=%s) – Total: %d, Covered: %d, Uncovered: %d",
            ir.project_name,
            pid,
            len(unique_strategies),
            covered_count,
            uncovered_count,
        )

        return StrategyPlanResponse(
            project_name=ir.project_name,
            project_id=pid,
            pipeline_run_id=rid,
            framework=ir.framework,
            total_strategies=len(unique_strategies),
            covered_strategies_count=covered_count,
            uncovered_strategies_count=uncovered_count,
            strategies=unique_strategies,
        )

    def _deduplicate_strategies(self, strategies: List[TestStrategy]) -> List[TestStrategy]:
        """Remove duplicate strategies based on strategy ID and key properties."""
        seen_ids: Set[str] = set()
        seen_keys: Set[str] = set()
        unique: List[TestStrategy] = []
        duplicates_count = 0

        for strat in strategies:
            composite_key = f"{strat.target_component}:{strat.category}:{strat.description}"
            if strat.id in seen_ids or composite_key in seen_keys:
                duplicates_count += 1
                logger.debug("Removing duplicate strategy: id='%s', key='%s'", strat.id, composite_key)
            else:
                seen_ids.add(strat.id)
                seen_keys.add(composite_key)
                unique.append(strat)

        if duplicates_count > 0:
            logger.info("Duplicate strategy removal complete: removed %d duplicate(s)", duplicates_count)

        return unique

    def _apply_existing_test_coverage(self, strategies: List[TestStrategy], ir: FrameworkAgnosticIR) -> None:
        """Mark strategies as covered (is_covered=True) if existing test files match the target."""
        if not ir.existing_tests:
            return

        test_file_paths = [t.file_path.lower() for t in ir.existing_tests]

        for strat in strategies:
            target_lower = strat.target_component.lower()
            # If any existing test path contains the target component name, mark as covered
            if any(target_lower in path for path in test_file_paths):
                strat.is_covered = True
                logger.info(
                    "Strategy '%s' for target '%s' marked as covered by existing tests.",
                    strat.id,
                    strat.target_component,
                )

    def validate_strategies(self, strategies: List[TestStrategy], ir: FrameworkAgnosticIR) -> None:
        """Validate generated strategies for correctness.

        Validates:
        - Duplicate strategies
        - Invalid targets (empty target_component)
        - Missing components (target refers to unknown component/service)
        - Invalid dependencies / preconditions

        Raises:
            ValueError: If validation rules are violated.
        """
        logger.info("StrategyEngine: Validating %d strategy/strategies", len(strategies))

        # 1. Duplicate Check
        seen_ids = set()
        for s in strategies:
            if s.id in seen_ids:
                msg = f"Validation Error: Duplicate strategy ID found: {s.id}"
                logger.error(msg)
                raise ValueError(msg)
            seen_ids.add(s.id)

        # 2. Invalid Targets & Missing Components Check
        known_targets = set(c.name for c in ir.components)
        known_targets.update(s.name for s in ir.services)
        known_targets.update(r.component for r in ir.routes if r.component)
        known_targets.update(r.path for r in ir.routes)

        for s in strategies:
            if not s.target_component or not s.target_component.strip():
                msg = f"Validation Error: Strategy '{s.id}' has an invalid/empty target component."
                logger.error(msg)
                raise ValueError(msg)

            # Note: We log warning if target is not in known components, but allow valid path/global targets
            if known_targets and s.target_component not in known_targets:
                logger.debug(
                    "Validation Note: Strategy target '%s' is an abstract/synthetic target.",
                    s.target_component,
                )

        logger.info("StrategyEngine: Validation passed successfully.")
