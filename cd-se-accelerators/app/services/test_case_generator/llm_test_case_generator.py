"""
LLM Test Case Generator – Module 7 Hybrid Layer.

Uses Groq LLM to reason about component behavior, state interactions, and edge cases
to generate rich, human-readable test case specifications while maintaining strict
Pydantic schema validation and traceability metadata.
"""

import logging
from typing import Any, Dict, List, Optional
from app.models.strategy_models import StrategyPlanResponse, TestStrategy
from app.models.edge_case_models import EdgeCasePlanResponse, EdgeCaseScenario
from app.models.test_case_models import (
    TestCase,
    TestCaseLocator,
    TestCaseMetadata,
    TestCasePlanResponse,
    TestCaseStep,
    TestCaseTraceability,
)
from app.services.llm_client import GroqLLMClient

logger = logging.getLogger(__name__)


def _extract_traceability(strategy: TestStrategy, edge_case: EdgeCaseScenario) -> TestCaseTraceability:
    """Helper to construct traceability object."""
    comp_id = strategy.component_id or edge_case.component_id or f"comp_{strategy.target_component}"
    return TestCaseTraceability(
        strategy_id=strategy.id,
        edge_case_id=edge_case.id,
        component_id=comp_id,
        project_id=strategy.project_id or getattr(edge_case, "project_id", None),
        pipeline_run_id=strategy.pipeline_run_id or getattr(edge_case, "pipeline_run_id", None),
        source_file=strategy.source_file or getattr(edge_case, "source_file", None),
        element_id=strategy.element_id or edge_case.element_id,
        event_id=strategy.event_id or edge_case.event_id,
        state_id=strategy.state_id or edge_case.state_id,
        service_id=strategy.service_id or edge_case.service_id,
        route_id=strategy.route_id or edge_case.route_id,
    )


class LLMTestCaseGenerator:
    """Hybrid LLM Test Case Generator using Groq LLM with deterministic validation."""

    def __init__(self, llm_client: Optional[GroqLLMClient] = None):
        self.llm_client = llm_client or GroqLLMClient()

    def generate_llm_test_cases(
        self,
        strategy_plan: StrategyPlanResponse,
        edge_case_plan: Optional[EdgeCasePlanResponse] = None,
        frontend_context: Optional[Any] = None,
    ) -> Optional[List[TestCase]]:
        """Generate semantic test cases using Groq LLM based on strategy and edge case plans.

        Returns:
            List of validated TestCase instances, or None if LLM is unavailable or fails.
        """
        if not self.llm_client.is_available:
            logger.info("LLMTestCaseGenerator: Groq LLM unavailable. Skipping LLM generation step.")
            return None

        strategies = getattr(strategy_plan, "strategies", []) or []
        edge_cases = getattr(edge_case_plan, "edge_cases", []) if edge_case_plan else []

        if not strategies:
            return None

        # Build strategy & edge case mapping by strategy_id
        ec_map: Dict[str, List[EdgeCaseScenario]] = {}
        for ec in edge_cases:
            sid = getattr(ec, "strategy_id", None)
            if sid:
                ec_map.setdefault(sid, []).append(ec)

        logger.info("LLMTestCaseGenerator: Generating test cases via Groq LLM for %d strategies.", len(strategies))

        generated_test_cases: List[TestCase] = []

        # Process components/strategies in focused batches
        for strat in strategies[:15]:  # Process target strategies
            associated_ecs = ec_map.get(strat.id, [])
            if not associated_ecs:
                # Synthesize fallback edge case scenario
                associated_ecs = [
                    EdgeCaseScenario(
                        id=f"EC-{strat.id}-001",
                        strategy_id=strat.id,
                        category=strat.category,
                        title=f"Standard execution for {strat.target_component}",
                        description=f"Verify {strat.target_component} operates under standard inputs.",
                        expected_behavior=f"{strat.target_component} renders and handles events cleanly.",
                        tags=list(strat.coverage_tags),
                    )
                ]

            for ec in associated_ecs[:2]:
                tc = self._generate_single_llm_test_case(strat, ec, frontend_context)
                if tc:
                    generated_test_cases.append(tc)

        if generated_test_cases:
            logger.info("LLMTestCaseGenerator: Successfully generated %d valid test cases via Groq LLM.", len(generated_test_cases))
            return generated_test_cases

        return None

    def _generate_single_llm_test_case(
        self,
        strategy: TestStrategy,
        edge_case: EdgeCaseScenario,
        frontend_context: Optional[Any] = None,
    ) -> Optional[TestCase]:
        """Query Groq LLM for a specific strategy & edge case combination."""
        comp = strategy.target_component
        trace_obj = _extract_traceability(strategy, edge_case)

        from app.services.test_case_generator.testcase_prompt import SYSTEM_PROMPT, build_testcase_prompt

        ir_summary = f"Component: {comp}\nSource File: {strategy.source_file or 'Unknown'}\nTarget Element: {strategy.element_id or 'container'}"
        strat_info = f"Strategy ID: {strategy.id}\nCategory: {strategy.category}\nTarget: {comp}\nPreconditions: {strategy.preconditions}"
        ec_info = f"Edge Case ID: {edge_case.id}\nTitle: {edge_case.title}\nScenario: {edge_case.description}\nExpected Outcome: {edge_case.expected_behavior}"

        prompt = build_testcase_prompt(
            ir_summary=ir_summary,
            strategy_info=strat_info,
            edge_case_info=ec_info,
            target_component=comp,
        )

        resp_json = self.llm_client.generate_json(prompt, system_prompt=SYSTEM_PROMPT)

        if not resp_json or not isinstance(resp_json, dict):
            return None

        try:
            # Construct validated TestCase
            tc_id = f"TC-{strategy.id}-{edge_case.id.replace('EC-' + strategy.id + '-', '')}"
            steps_raw = resp_json.get("steps", [])
            steps_list = [str(s) for s in steps_raw] if isinstance(steps_raw, list) else [str(steps_raw)]

            loc_raw = resp_json.get("element_locator", {})
            loc_obj = TestCaseLocator(
                strategy=loc_raw.get("strategy", "role") if isinstance(loc_raw, dict) else "role",
                value=loc_raw.get("value", "button") if isinstance(loc_raw, dict) else "button",
            )

            metadata_obj = TestCaseMetadata(
                component=comp,
                element=loc_obj.value,
                element_type="element",
                locator=loc_obj,
                action=resp_json.get("action", "render"),
                assertion_type=resp_json.get("assertion_type", "exists"),
                assertion_target=loc_obj.value,
                expected_value=resp_json.get("expected_result", edge_case.expected_behavior),
                mock_required=False,
                mock_services=[],
            )

            tc = TestCase(
                id=tc_id,
                strategy_id=strategy.id,
                edge_case_id=edge_case.id,
                category=edge_case.category or strategy.category or "General",
                priority=strategy.priority or "Medium",
                component=comp,
                title=resp_json.get("title") or f"Component: {comp} - {edge_case.title}",
                objective=resp_json.get("objective") or f"Verify {comp} behavior under {edge_case.title}",
                preconditions=resp_json.get("preconditions") or list(strategy.preconditions),
                steps=steps_list,
                test_data=resp_json.get("test_data") or dict(edge_case.input_data or {}),
                expected_result=resp_json.get("expected_result") or edge_case.expected_behavior,
                tags=list(set(list(strategy.coverage_tags) + list(edge_case.tags) + ["llm-generated"])),
                metadata=metadata_obj,
                traceability=trace_obj,
            )

            return tc
        except Exception as exc:
            logger.warning("LLMTestCaseGenerator validation error: %s", exc)
            return None
