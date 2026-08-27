"""Stage 4 test-generation orchestration."""

import json
import logging
import math
import re
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Protocol

from pydantic import BaseModel, ValidationError

from app.agents.code_understanding.client import (
    AllProvidersExhaustedError,
    ProviderTokenBudgetError,
    TruncatedStructuredResponseError,
)
from ...schemas.enums import Category
from ...schemas.test_case import TestCase, TestCaseBatch
from .category_engine import CategoryEngine
from .coverage_analyzer import CoverageAnalyzer
from .deduplicator import Deduplicator
from .priority_engine import PriorityEngine
from .prompt_builder import PromptBuilder
from .scenario_planner import ExecutableScenarioPlanner, PLANNER_VERSION
from .traceability_mapper import TraceabilityMapper
from .lifecycle_detector import LifecycleDetector
from .deterministic_unit_generator import DeterministicUnitTestGenerator

logger = logging.getLogger(__name__)

TEST_GENERATION_SYSTEM_PROMPT = (
    "Return only one valid JSON object matching the supplied JSON schema exactly. "
    "Do not include markdown, code fences, comments, or explanatory text. Preserve "
    "every required field, use only enum values allowed by the schema, and do not "
    "include additional properties."
)
TEST_GENERATION_RESPONSE_MODEL = TestCaseBatch


class TestGenerationError(RuntimeError):
    """Raised when Stage 4 cannot produce a valid result."""


class TestGenerationTruncatedError(TestGenerationError):
    """Raised when a generation batch exceeds the provider output limit."""


class TestGenerationProviderExhaustedError(TestGenerationError):
    """Raised when every configured generation provider is unavailable."""

    def __init__(self, reason: str) -> None:
        super().__init__(reason)
        self.reason = reason


class StructuredTestGenerationClient(Protocol):
    def generate_structured(
        self, *, system_prompt: str, user_prompt: str, response_model: type[BaseModel],
        max_completion_tokens: int | None = None,
    ) -> BaseModel: ...


class TestGenerationAgent:
    """Generate and post-process test cases from a Stage 3 artifact."""

    def __init__(
        self,
        model_name: str = "mixtral-8x7b-32768",
        *,
        client: StructuredTestGenerationClient | None = None,
        prompt_builder: PromptBuilder | None = None,
        category_engine: CategoryEngine | None = None,
        priority_engine: PriorityEngine | None = None,
        deduplicator: Deduplicator | None = None,
        coverage_analyzer: CoverageAnalyzer | None = None,
        traceability_mapper: TraceabilityMapper | None = None,
        lifecycle_detector: LifecycleDetector | None = None,
        scenario_planner: ExecutableScenarioPlanner | None = None,
        unit_generator: DeterministicUnitTestGenerator | None = None,
        deterministic_mode: bool = False,
        max_batch_functions: int = 4,
        estimated_tokens_per_case: int = 650,
        safe_output_tokens: int = 12_000,
    ) -> None:
        self.model_name = model_name  # Retained for source compatibility.
        self._client = client
        self._prompt_builder = prompt_builder or PromptBuilder()
        self._category_engine = category_engine or CategoryEngine()
        self._priority_engine = priority_engine or PriorityEngine()
        self._deduplicator = deduplicator or Deduplicator()
        self._coverage_analyzer = coverage_analyzer or CoverageAnalyzer()
        self._traceability_mapper = traceability_mapper or TraceabilityMapper()
        self._lifecycle_detector = lifecycle_detector or LifecycleDetector()
        self._scenario_planner = scenario_planner or ExecutableScenarioPlanner()
        self._unit_generator = unit_generator or DeterministicUnitTestGenerator()
        self._deterministic_mode = deterministic_mode
        self._max_batch_functions = max_batch_functions
        self._estimated_tokens_per_case = estimated_tokens_per_case
        self._safe_output_tokens = safe_output_tokens

    def cache_fingerprint(self) -> dict[str, Any]:
        """Return every stable agent setting that influences generation output.

        Returns:
            JSON-compatible prompt, model, batching, and token-budget settings.
        """
        return {
            "model_name": self.model_name,
            "prompt_hash": self._prompt_builder.cache_fingerprint(),
            "system_prompt": TEST_GENERATION_SYSTEM_PROMPT,
            "max_batch_functions": self._max_batch_functions,
            "estimated_tokens_per_case": self._estimated_tokens_per_case,
            "safe_output_tokens": self._safe_output_tokens,
            "scenario_planner_version": PLANNER_VERSION,
            "unit_generator_version": self._unit_generator.VERSION,
            "deterministic_mode": self._deterministic_mode,
            "categories": [item.value for item in Category],
        }

    @staticmethod
    def is_current_output(
        output: object, stage3_payload: dict[str, Any]
    ) -> bool:
        """Return whether persisted Stage 4 output used the active planner."""
        if not isinstance(output, dict):
            return False
        cases = output.get("generated_test_cases")
        if not isinstance(cases, list):
            return False
        return bool(cases) and all(
            isinstance(case, dict)
            and isinstance(case.get("unit_test"), dict)
            and isinstance(case.get("traceability"), dict)
            and case["traceability"].get("stage4_generator_version")
            == DeterministicUnitTestGenerator.VERSION
            for case in cases
        )

    def _call_llm(
        self, prompt: str, estimated_cases: int = 1, *,
        capacity_aware: bool = False,
    ) -> str:
        if self._client is None:
            raise TestGenerationError("A test-generation client is required")
        try:
            logger.info(
                "Invoking structured test generation prompt_length=%d "
                "response_model=%s estimated_cases=%d requested_completion_tokens=%d",
                len(prompt),
                TEST_GENERATION_RESPONSE_MODEL.__name__,
                estimated_cases,
                self._completion_budget(estimated_cases),
            )
            capacity_method = getattr(
                type(self._client),
                "generate_structured_capacity_aware",
                None,
            )
            method = (
                self._client.generate_structured_capacity_aware
                if capacity_aware and callable(capacity_method)
                else self._client.generate_structured
            )
            response = method(
                system_prompt=TEST_GENERATION_SYSTEM_PROMPT,
                user_prompt=prompt,
                response_model=TEST_GENERATION_RESPONSE_MODEL,
                max_completion_tokens=self._completion_budget(estimated_cases),
            )
            return TEST_GENERATION_RESPONSE_MODEL.model_validate(
                response
            ).model_dump_json()
        except TestGenerationError:
            raise
        except TruncatedStructuredResponseError as error:
            raise TestGenerationTruncatedError(
                "Test-generation response truncated due to token limit"
            ) from error
        except AllProvidersExhaustedError as error:
            raise TestGenerationProviderExhaustedError(error.reason) from error
        except ProviderTokenBudgetError as error:
            raise TestGenerationProviderExhaustedError(
                "provider_token_budget_exhausted"
            ) from error
        except Exception as error:
            logger.exception("Test-generation provider failed")
            raise TestGenerationError("Test-generation provider failed") from error

    def _parse_llm_output(self, raw_json: str) -> list[TestCase]:
        try:
            data = json.loads(raw_json)
            if isinstance(data, list):  # Compatibility with early Stage 4 clients.
                data = {"test_cases": data}
            return TestCaseBatch.model_validate(data).test_cases
        except (json.JSONDecodeError, TypeError, ValidationError) as error:
            raise TestGenerationError("Invalid test-generation JSON") from error

    def _completion_budget(self, estimated_cases: int) -> int:
        return max(
            1_024,
            min(
                self._safe_output_tokens,
                int(estimated_cases * self._estimated_tokens_per_case * 1.2),
            ),
        )

    def generate(
        self, stage3_payload: dict[str, Any], categories: list[str] | None = None
    ) -> dict[str, Any]:
        # Stage 4 is intentionally deterministic. ``categories`` and the legacy
        # structured-output client remain accepted for API compatibility only.
        if self._deterministic_mode or self._client is None:
            return self._unit_generator.generate(stage3_payload)
        # Explicitly injected legacy clients remain supported for compatibility
        # with stored workflows during migration; production wiring is deterministic.
        if "regeneration_plan" in stage3_payload:
            try:
                return self._generate_single(stage3_payload, categories)
            except TestGenerationProviderExhaustedError as error:
                return self._partial_result(stage3_payload, reason=error.reason)
        batches = self._generation_batches(stage3_payload)
        if len(batches) == 1:
            return self._generate_scope_with_split(batches[0], categories)

        generated_cases: list[TestCase] = []
        total_generated = 0
        generation_reason: str | None = None

        def generate_batch(item: tuple[int, dict[str, Any]]) -> dict[str, Any]:
            index, batch = item
            logger.info(
                "Test generation batch=%d/%d targets=%d estimated_cases=%d",
                index, len(batches), len(batch.get("test_targets", [])),
                self._estimated_case_count(batch.get("test_targets", [])),
            )
            return self._generate_scope_with_split(batch, categories)

        indexed_batches = list(enumerate(batches, start=1))
        with ThreadPoolExecutor(max_workers=min(len(batches), 8)) as executor:
            batch_results = executor.map(generate_batch, indexed_batches)

        for (index, _), result in zip(
            indexed_batches, batch_results, strict=True
        ):
            generation_reason = generation_reason or result.get("generation_reason")
            total_generated += result["total_generated"]
            for item in result["generated_test_cases"]:
                case = TestCase.model_validate(item)
                if any(existing.id == case.id for existing in generated_cases):
                    case = case.model_copy(update={"id": f"B{index}-{case.id}"})
                generated_cases.append(case)

        traced = self._post_process(generated_cases, stage3_payload)
        remaining = self._coverage_analyzer.completion_gaps(traced, stage3_payload)
        return {
            "generated_test_cases": [case.model_dump(mode="json") for case in traced],
            "coverage_summary": self._coverage_analyzer.analyze(traced, stage3_payload),
            "total_generated": total_generated,
            "total_after_deduplication": len(traced),
            "generation_status": (
                "partial_coverage_incomplete" if remaining else "complete"
            ),
            "generation_reason": generation_reason,
            "uncovered_requirements": remaining,
        }

    def _generate_scope_with_split(
        self, stage3_payload: dict[str, Any], categories: list[str] | None
    ) -> dict[str, Any]:
        try:
            return self._generate_single(stage3_payload, categories)
        except TestGenerationProviderExhaustedError as error:
            logger.warning(
                "Test-generation providers exhausted; returning partial result "
                "reason=%s targets=%d",
                error.reason, len(stage3_payload.get("test_targets", [])),
            )
            return self._partial_result(stage3_payload, reason=error.reason)
        except TestGenerationTruncatedError:
            targets = stage3_payload.get("test_targets", [])
            if len(targets) <= 1:
                logger.warning(
                    "Test-generation batch cannot be split further; returning "
                    "partial result targets=%d",
                    len(targets),
                )
                return self._partial_result(
                    stage3_payload, reason="generation_truncated"
                )
            midpoint = len(targets) // 2
            logger.warning(
                "Retrying truncated test-generation response as two smaller batches "
                "original_targets=%d",
                len(targets),
            )
            left = self._generate_scope_with_split(
                {**stage3_payload, "test_targets": targets[:midpoint]}, categories
            )
            right = self._generate_scope_with_split(
                {**stage3_payload, "test_targets": targets[midpoint:]}, categories
            )
            cases = [
                TestCase.model_validate(item)
                for result in (left, right)
                for item in result["generated_test_cases"]
            ]
            for index, case in enumerate(cases):
                if any(previous.id == case.id for previous in cases[:index]):
                    cases[index] = case.model_copy(update={"id": f"S{index + 1}-{case.id}"})
            traced = self._post_process(cases, stage3_payload)
            remaining = self._coverage_analyzer.completion_gaps(
                traced, stage3_payload
            )
            return {
                "generated_test_cases": [case.model_dump(mode="json") for case in traced],
                "coverage_summary": self._coverage_analyzer.analyze(traced, stage3_payload),
                "total_generated": left["total_generated"] + right["total_generated"],
                "total_after_deduplication": len(traced),
                "generation_status": (
                    "partial_coverage_incomplete" if remaining else "complete"
                ),
                "generation_reason": (
                    left.get("generation_reason") or right.get("generation_reason")
                ),
                "uncovered_requirements": remaining,
            }

    def _partial_result(
        self, stage3_payload: dict[str, Any], *, reason: str
    ) -> dict[str, Any]:
        gaps = self._coverage_analyzer.completion_gaps([], stage3_payload)
        targets = stage3_payload.get("test_targets", [])
        return {
            "generated_test_cases": [],
            "coverage_summary": self._coverage_analyzer.analyze([], stage3_payload),
            "total_generated": 0,
            "total_after_deduplication": 0,
            "generation_status": "partial_coverage_incomplete",
            "generation_reason": reason,
            "uncovered_requirements": gaps or [
                {
                    "symbol": target.get("symbol", "unknown"),
                    "requirement": reason,
                    "category": "positive",
                    "requirement_id": f"{target.get('symbol', 'unknown')}|{reason}",
                }
                for target in targets
            ],
        }

    def _generation_batches(self, stage3_payload: dict[str, Any]) -> list[dict[str, Any]]:
        targets = stage3_payload.get("test_targets", [])
        if not targets:
            return [stage3_payload]
        max_estimated_cases = max(
            1, self._safe_output_tokens // self._estimated_tokens_per_case
        )
        batches: list[list[dict[str, Any]]] = []
        current: list[dict[str, Any]] = []
        current_cases = 0
        for target in sorted(targets, key=lambda item: (item.get("file", ""), item.get("symbol", ""))):
            estimated = self._estimated_case_count([target])
            module_changed = current and current[-1].get("file") != target.get("file")
            exceeds = (
                len(current) >= self._max_batch_functions
                or current_cases + estimated > max_estimated_cases
            )
            if current and (module_changed or exceeds):
                batches.append(current)
                current, current_cases = [], 0
            current.append(target)
            current_cases += estimated
        if current:
            batches.append(current)
        logger.info(
            "Generation sizing targets=%d estimated_cases=%d safe_output_tokens=%d "
            "batch_count=%d",
            len(targets), self._estimated_case_count(targets),
            self._safe_output_tokens, len(batches),
        )
        return [{**stage3_payload, "test_targets": batch} for batch in batches]

    @staticmethod
    def _estimated_case_count(targets: list[dict[str, Any]]) -> int:
        return sum(
            max(1, 2 * len([*target.get("branches", []), *target.get("edge_cases", [])]))
            for target in targets
        )

    def _generate_single(
        self, stage3_payload: dict[str, Any], categories: list[str] | None = None
    ) -> dict[str, Any]:
        requested = (
            [category.value for category in (
                Category.POSITIVE, Category.NEGATIVE, Category.BOUNDARY,
                Category.SECURITY, Category.EXCEPTION_INTEGRATION,
            )]
            if categories is None
            else categories
        )
        is_regeneration = "regeneration_plan" in stage3_payload
        if is_regeneration and categories is None:
            requested = stage3_payload["regeneration_plan"].get(
                "missing_categories", []
            )
        legacy_categories = {
            "functional": "positive", "regression": "positive",
            "performance": "boundary", "edge_case": "boundary",
            "validation": "negative", "integration": "exception/integration",
            "exception": "exception/integration",
        }
        requested = [legacy_categories.get(item, item) for item in requested]
        lifecycle_behaviors = (
            []
            if is_regeneration
            else self._lifecycle_detector.detect(stage3_payload)
        )
        prompt_payload = (
            {"regeneration_feedback": self._regeneration_context(stage3_payload)}
            if is_regeneration
            else {
                "generation_context": self._generation_context(
                    stage3_payload, lifecycle_behaviors
                )
            }
        )
        if is_regeneration:
            prompt_payload["existing_test_case_count"] = stage3_payload.get(
                "existing_test_case_count", 0
            )
            prompt_payload["requested_regenerated_count"] = stage3_payload.get(
                "requested_regenerated_count",
                len(stage3_payload["regeneration_plan"].get("actions", [])),
            )
        prompt = self._prompt_builder.build_prompt(prompt_payload, requested)
        estimated_cases = (
            prompt_payload.get("requested_regenerated_count", 0)
            or self._estimated_case_count(stage3_payload.get("test_targets", []))
            or 1
        )
        generated = self._parse_llm_output(
            self._call_llm(
                prompt, estimated_cases, capacity_aware=is_regeneration
            )
        )
        logger.info(
            "Test generation completed existing_test_cases=%d "
            "requested_regenerated_cases=%d generated_cases=%d",
            prompt_payload.get("existing_test_case_count", 0),
            prompt_payload.get("requested_regenerated_count", 0),
            len(generated),
        )
        total_generated = len(generated)
        generated = self._lifecycle_detector.filter_supported(
            generated, lifecycle_behaviors
        )
        traced = self._post_process(generated, stage3_payload)
        generation_reason: str | None = None
        if not is_regeneration:
            previous_gap_count: int | None = None
            no_progress_passes = 0
            for completion_pass in range(1, 3):
                gaps = self._coverage_analyzer.completion_gaps(traced, stage3_payload)
                if not gaps:
                    break
                if previous_gap_count is not None and len(gaps) >= previous_gap_count:
                    no_progress_passes += 1
                else:
                    no_progress_passes = 0
                if no_progress_passes >= 2:
                    logger.warning(
                        "Generation completion stopped after no progress "
                        "uncovered_requirements=%d pass=%d",
                        len(gaps), completion_pass,
                    )
                    break
                previous_gap_count = len(gaps)
                completion_payload = {
                    **prompt_payload,
                    "coverage_completion_gaps": gaps,
                    "requested_regenerated_count": len(gaps),
                }
                logger.info(
                    "Generation completion pass=%d uncovered_requirements=%d",
                    completion_pass, len(gaps),
                )
                try:
                    additions = self._parse_llm_output(
                        self._call_llm(
                            self._prompt_builder.build_prompt(completion_payload, requested),
                            len(gaps),
                        )
                    )
                except TestGenerationTruncatedError:
                    logger.warning(
                        "Generation completion truncated; preserving partial suite "
                        "pass=%d uncovered_requirements=%d",
                        completion_pass, len(gaps),
                    )
                    break
                except TestGenerationProviderExhaustedError as error:
                    generation_reason = error.reason
                    logger.warning(
                        "Generation completion providers exhausted; preserving "
                        "partial suite pass=%d reason=%s uncovered_requirements=%d",
                        completion_pass, error.reason, len(gaps),
                    )
                    break
                total_generated += len(additions)
                processed_additions = self._post_process(additions, stage3_payload)
                processed_additions = self._tag_completion_requirements(
                    processed_additions, gaps
                )
                updated = self._post_process(
                    [*traced, *processed_additions], stage3_payload
                )
                next_gap_count = len(
                    self._coverage_analyzer.completion_gaps(updated, stage3_payload)
                )
                logger.info(
                    "Generation completion progress pass=%d before=%d after=%d",
                    completion_pass, len(gaps), next_gap_count,
                )
                traced = updated
            remaining = self._coverage_analyzer.completion_gaps(traced, stage3_payload)
        else:
            remaining = []
        return {
            "generated_test_cases": [case.model_dump(mode="json") for case in traced],
            "coverage_summary": self._coverage_analyzer.analyze(traced, stage3_payload),
            "total_generated": total_generated,
            "total_after_deduplication": len(traced),
            "generation_status": (
                "partial_coverage_incomplete" if remaining else "complete"
            ),
            "generation_reason": generation_reason,
            "uncovered_requirements": remaining,
        }

    @staticmethod
    def _generation_context(
        stage3: dict[str, Any],
        lifecycle_behaviors: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        """Select only source-grounding facts related to the current targets."""
        targets = stage3.get("test_targets", [])
        target_symbols = {
            item.get("symbol") for item in targets if item.get("symbol")
        }
        target_files = {item.get("file") for item in targets if item.get("file")}
        compact_targets = [
            {
                key: target[key]
                for key in (
                    "symbol", "file", "signature", "branches", "edge_cases"
                )
                if target.get(key) not in (None, [], "")
            }
            for target in targets
        ]
        target_keys = {
            (target.get("symbol"), target.get("file")) for target in compact_targets
        }
        for behavior in lifecycle_behaviors or []:
            key = (behavior.get("symbol"), behavior.get("file"))
            branch = ": ".join(
                part for part in (
                    behavior.get("type"), behavior.get("evidence")
                ) if part
            )
            existing = next(
                (
                    target for target in compact_targets
                    if (target.get("symbol"), target.get("file")) == key
                ),
                None,
            )
            if existing is not None:
                existing.setdefault("branches", []).append(branch)
            elif key not in target_keys:
                compact_targets.append({
                    key: value for key, value in {
                        "symbol": behavior.get("symbol"),
                        "file": behavior.get("file"),
                        "branches": [branch] if branch else [],
                    }.items() if value not in (None, [], "")
                })
                target_keys.add(key)
        endpoints = [
            endpoint
            for endpoint in stage3.get("api_endpoints", [])
            if endpoint.get("handler") in target_symbols
            or endpoint.get("file") in target_files
        ]
        rules = [
            rule
            for rule in stage3.get("business_rules", [])
            if target_symbols.intersection(rule.get("symbols", []))
            or target_files.intersection(rule.get("files", []))
        ]
        endpoint_models = {
            name
            for endpoint in endpoints
            for name in (
                endpoint.get("request_type"), endpoint.get("response_type")
            )
            if name
        }
        models = [
            model
            for model in stage3.get("data_models", [])
            if model.get("name") in endpoint_models
            or model.get("file") in target_files
        ]
        return {
            "targets": compact_targets,
            "api_endpoints": endpoints,
            "business_rules": rules,
            "data_models": models,
        }

    @staticmethod
    def _regeneration_context(payload: dict[str, Any]) -> dict[str, Any]:
        """Build minimal target grounding and Stage 5 repair feedback."""
        plan = payload.get("regeneration_plan", {})
        actions = [
            action for action in plan.get("actions", [])
            if action.get("action") != "REMOVE"
        ]
        cases_by_id = {
            case.get("id"): case
            for case in payload.get("test_cases_to_improve", [])
            if case.get("id")
        }
        verification = payload.get("regeneration_verification", {})
        verification_by_id = {
            result.get("test_case_id"): result
            for result in verification.get("results", [])
            if result.get("test_case_id")
        }

        target_symbols: list[str] = []
        target_files: set[str] = set()
        feedback = []
        feedback_before_reduction = []
        for action in actions:
            case_id = action.get("test_case_id")
            case = cases_by_id.get(case_id, {})
            trace = case.get("traceability") or {}
            result = verification_by_id.get(case_id, {})
            evidence = result.get("evidence", [])
            symbol = (
                action.get("target_symbol")
                or trace.get("symbol")
                or next(iter(trace.get("symbols", [])), None)
                or next(
                    (
                        item.get("symbol") for item in evidence
                        if item.get("symbol")
                    ),
                    None,
                )
            )
            if symbol and symbol not in target_symbols:
                target_symbols.append(symbol)
            target_files.update(
                item for item in (
                    trace.get("file"),
                    *trace.get("source_files", []),
                    *(item.get("file") for item in evidence),
                )
                if item
            )
            failure_reasons = [
                finding.get("detail")
                for finding in result.get("findings", [])
                if finding.get("status") != "Verified" and finding.get("detail")
            ]
            missing_coverage = action.get("coverage_requirement")
            if missing_coverage is None and action.get("action") == "ADD":
                missing_coverage = action.get("category")
            feedback_item = {
                key: value for key, value in {
                    "failed_test_id": case_id,
                    "verification_status": result.get("status"),
                    "failure_reason": failure_reasons,
                    "missing_coverage": missing_coverage,
                    "target_symbol": symbol,
                }.items() if value not in (None, [], "")
            }
            feedback_before_reduction.append({
                **feedback_item,
                **(
                    {"verification_evidence": evidence}
                    if evidence
                    else {}
                ),
            })
            feedback.append(feedback_item)

        feedback_before_bytes = len(json.dumps(
            feedback_before_reduction,
            ensure_ascii=False,
            separators=(",", ":"),
        ).encode("utf-8"))
        feedback_after_bytes = len(json.dumps(
            feedback,
            ensure_ascii=False,
            separators=(",", ":"),
        ).encode("utf-8"))
        bytes_saved = feedback_before_bytes - feedback_after_bytes
        logger.info(
            "Regeneration feedback reduction "
            "before_bytes=%d after_bytes=%d bytes_saved=%d "
            "estimated_tokens_saved=%d",
            feedback_before_bytes,
            feedback_after_bytes,
            bytes_saved,
            math.ceil(bytes_saved / 4),
        )

        targets = [
            target for target in payload.get("test_targets", [])
            if target.get("symbol") in target_symbols
            or target.get("file") in target_files
        ]
        selected = TestGenerationAgent._generation_context(
            {**payload, "test_targets": targets}
        )
        grounding = {
            "targets": selected["targets"],
            "data_models": selected["data_models"],
            "api_endpoints": selected["api_endpoints"],
            "analyzed_files": [
                {"path": item["path"]}
                for item in payload.get("analyzed_files", [])
                if item.get("path") in {
                    target.get("file") for target in targets
                }
                or set(item.get("key_symbols", [])).intersection(target_symbols)
            ],
        }
        return {
            "grounding": grounding,
            "feedback": feedback,
        }

    def estimate_regeneration_prompt_tokens(
        self, payload: dict[str, Any]
    ) -> int:
        """Estimate the exact compact Stage 6 regeneration prompt size."""
        prompt_payload = {
            "regeneration_feedback": self._regeneration_context(payload),
            "existing_test_case_count": payload.get(
                "existing_test_case_count", 0
            ),
            "requested_regenerated_count": payload.get(
                "requested_regenerated_count",
                len(payload.get("regeneration_plan", {}).get("actions", [])),
            ),
        }
        categories = payload.get("regeneration_plan", {}).get(
            "missing_categories", []
        )
        prompt = self._prompt_builder.build_prompt(
            prompt_payload, categories
        )
        return max(1, len(prompt.encode("utf-8")) // 4)

    def _tag_completion_requirements(
        self, cases: list[TestCase], gaps: list[dict[str, str]]
    ) -> list[TestCase]:
        tagged = list(cases)
        for gap in gaps:
            if gap["requirement"] == "function":
                continue
            branch_tokens = {
                item.casefold()
                for item in re.findall(r"[A-Za-z0-9]+", gap["requirement"])
                if len(item) > 2
            }
            numeric_tokens = {item for item in branch_tokens if item.isdigit()}
            best: tuple[float, int] | None = None
            for index, case in enumerate(tagged):
                if gap["symbol"] not in self._coverage_analyzer._symbols(case):
                    continue
                accepted = {gap["category"]}
                if gap["category"] == Category.NEGATIVE.value:
                    accepted.add(Category.BOUNDARY.value)
                if case.category.value not in accepted:
                    continue
                text_tokens = {
                    item.casefold()
                    for item in re.findall(
                        r"[A-Za-z0-9]+",
                        " ".join([case.title, case.description, *case.steps, *case.expected_results]),
                    )
                    if len(item) > 2
                }
                if not numeric_tokens.issubset(text_tokens):
                    continue
                score = len(branch_tokens & text_tokens) / len(branch_tokens) if branch_tokens else 1
                if score >= 0.3 and (best is None or score > best[0]):
                    best = (score, index)
            if best is not None:
                index = best[1]
                trace = dict(tagged[index].traceability or {})
                markers = list(trace.get("coverage_requirements", []))
                if gap["requirement_id"] not in markers:
                    markers.append(gap["requirement_id"])
                trace["coverage_requirements"] = markers
                tagged[index] = tagged[index].model_copy(
                    update={"traceability": trace}
                )
        return tagged

    def _post_process(
        self, generated: list[TestCase], stage3_payload: dict[str, Any]
    ) -> list[TestCase]:
        generated = self._filter_unsupported_http_tests(generated, stage3_payload)
        categorized = self._category_engine.assign(generated)
        prioritized = self._priority_engine.assign(categorized)
        traced = self._traceability_mapper.map(prioritized, stage3_payload)
        supported = self._filter_unsupported_expectations(
            traced, stage3_payload
        )
        canonical = self._canonicalize_scenarios(supported, stage3_payload)
        deduplicated = self._deduplicator.deduplicate(canonical)
        return self._scenario_planner.plan(deduplicated, stage3_payload)

    @staticmethod
    def _filter_unsupported_expectations(
        cases: list[TestCase], stage3_payload: dict[str, Any]
    ) -> list[TestCase]:
        endpoints = stage3_payload.get("api_endpoints", [])
        implementation_text = json.dumps(
            {
                "targets": stage3_payload.get("test_targets", []),
                "rules": stage3_payload.get("business_rules", []),
                "endpoints": endpoints,
            },
            default=str,
        ).casefold()
        result: list[TestCase] = []
        for case in cases:
            trace = case.traceability or {}
            route = trace.get("route")
            method = str(trace.get("method") or "").casefold()
            endpoint = next(
                (
                    item for item in endpoints
                    if item.get("route") == route
                    and (
                        not method
                        or str(item.get("method") or "").casefold() == method
                    )
                ),
                None,
            )
            claim = " ".join(
                [case.title, case.description, *case.steps, *case.expected_results]
            )
            status = re.search(
                r"\b(?:HTTP|status(?:\s+code)?)\s*[:=]?\s*([1-5]\d{2})\b",
                claim,
                re.I,
            )
            if status and endpoint:
                supported = {
                    *endpoint.get("success_status_codes", []),
                    *endpoint.get("error_status_codes", []),
                }
                if not endpoint.get("success_status_codes"):
                    supported.add(200)
                if int(status.group(1)) not in supported:
                    logger.warning(
                        "Discarding test id=%s with unsupported HTTP status=%s",
                        case.id, status.group(1),
                    )
                    continue
            if status and route and endpoint is None:
                logger.warning(
                    "Discarding test id=%s with unresolved endpoint=%s",
                    case.id, route,
                )
                continue
            if re.search(
                r"\b(?:authentication|required login|authorization|"
                r"unauthenticated|unauthorized|forbidden)\b",
                claim,
                re.I,
            ) and not re.search(
                r"\b(?:auth|login|token|credential|permission|security)\w*\b",
                implementation_text,
                re.I,
            ):
                logger.warning(
                    "Discarding unsupported authentication test id=%s",
                    case.id,
                )
                continue
            result.append(case)
        return result

    @staticmethod
    def _canonicalize_scenarios(
        cases: list[TestCase], stage3_payload: dict[str, Any]
    ) -> list[TestCase]:
        """Keep one metadata-consistent variant for each scenario."""
        endpoints = stage3_payload.get("api_endpoints", [])

        def preference(case: TestCase) -> tuple[int, int, int]:
            trace = case.traceability or {}
            endpoint = next(
                (
                    item for item in endpoints
                    if item.get("route") == trace.get("route")
                    and (
                        not trace.get("method")
                        or str(item.get("method") or "").casefold()
                        == str(trace.get("method")).casefold()
                    )
                ),
                {},
            )
            expected = Deduplicator._canonical_expected(
                " ".join(case.expected_results)
            )
            status = re.search(
                r"\b(?:HTTP|status(?:\s+code)?)\s*[:=]?\s*([1-5]\d{2})\b",
                " ".join(case.expected_results),
                re.I,
            )
            primary_statuses = (
                endpoint.get("error_status_codes", [])
                if Deduplicator._polarity(case) == "negative"
                else endpoint.get("success_status_codes", []) or [200]
            )
            status_rank = (
                2
                if status and int(status.group(1)) in primary_statuses[:1]
                else int(status is None or int(status.group(1)) in primary_statuses)
            )
            return (
                status_rank,
                int(expected not in {"", "success", "failure"}),
                len(case.expected_results),
            )

        selected: dict[tuple[str, str, str], TestCase] = {}
        order: list[tuple[str, str, str]] = []
        for case in cases:
            key = Deduplicator._scenario_key(case)
            if key not in selected:
                selected[key] = case
                order.append(key)
            elif preference(case) > preference(selected[key]):
                selected[key] = case
        return [selected[key] for key in order]

    @staticmethod
    def _filter_unsupported_http_tests(
        cases: list[TestCase], stage3_payload: dict[str, Any]
    ) -> list[TestCase]:
        if stage3_payload.get("api_endpoints"):
            return cases
        http_claim = re.compile(
            r"\b(?:http|https|endpoint|rest|status\s+code|response\s+code|"
            r"get\s+/|post\s+/|put\s+/|patch\s+/|delete\s+/|[1-5]\d\d\s+status)\b",
            re.IGNORECASE,
        )
        supported = []
        for case in cases:
            text = " ".join(
                [case.title, case.description, *case.steps, *case.expected_results]
            )
            trace = case.traceability or {}
            if http_claim.search(text) or any(
                trace.get(key) for key in ("route", "endpoint", "method", "api_routes")
            ):
                logger.warning(
                    "Discarding unsupported HTTP test case id=%s: no routes detected",
                    case.id,
                )
                continue
            supported.append(case)
        return supported


__all__ = ["TestGenerationAgent", "TestGenerationError"]
