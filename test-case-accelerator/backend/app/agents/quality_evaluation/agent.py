"""Stage 6 AI test-suite quality evaluation with deterministic fallback."""

from __future__ import annotations

import json
import hashlib
import logging
from collections import Counter
from typing import Any, Protocol

from pydantic import BaseModel

from app.schemas.enums import Category
from app.schemas.test_case import TestCase
from app.schemas.test_quality import (
    QualityDimensionScores,
    QualityEvaluation,
    QualityFeedback,
    RegenerationAction,
    RegenerationActionType,
    RegenerationPlan,
)
from app.schemas.test_verification import TestVerificationResult, VerificationStatus
from app.agents.test_generation.coverage_analyzer import CoverageAnalyzer
from app.agents.test_generation.deduplicator import Deduplicator

QUALITY_EVALUATION_PROMPT_VERSION = "1.1.0"
QUALITY_EVALUATION_SYSTEM_PROMPT = (
    "Evaluate this test suite for coverage, correctness, traceability, "
    "completeness, boundary coverage, negative testing, security, "
    "maintainability, and duplicate quality. Performance is outside this static "
    "pipeline and must not be scored or recommended. Return actionable structured "
    "feedback and identify only cases that need improvement or replacement."
)
QUALITY_SCORING_VERSION = "1.0.0"
logger = logging.getLogger(__name__)


class TestQualityEvaluationError(RuntimeError):
    """Raised when Stage 6 inputs cannot be evaluated."""


class StructuredQualityClient(Protocol):
    def generate_structured(
        self, *, system_prompt: str, user_prompt: str, response_model: type[BaseModel]
    ) -> BaseModel: ...


class TestQualityEvaluationAgent:
    def __init__(
        self, *, client: StructuredQualityClient | None = None,
        model_name: str = "unknown",
    ) -> None:
        self._client = client
        self._model_name = model_name

    def cache_fingerprint(self) -> dict[str, Any]:
        """Return prompt, model, and deterministic scoring configuration.

        Returns:
            JSON-compatible values affecting quality evaluation output.
        """
        return {
            "prompt_version": QUALITY_EVALUATION_PROMPT_VERSION,
            "prompt_hash": hashlib.sha256(
                QUALITY_EVALUATION_SYSTEM_PROMPT.encode("utf-8")
            ).hexdigest(),
            "model_name": self._model_name,
            "scoring_version": QUALITY_SCORING_VERSION,
            "scored_dimensions": [
                "coverage", "correctness", "traceability", "completeness",
                "duplicate_quality", "maintainability", "category_coverage",
                "boundary_coverage", "negative_testing", "security",
            ],
            "performance_weight": 0,
        }

    def evaluate(
        self,
        test_cases: list[TestCase] | list[dict[str, Any]],
        verification: TestVerificationResult | dict[str, Any],
        stage3_payload: dict[str, Any],
        *,
        threshold: float,
        iteration: int,
    ) -> QualityEvaluation:
        cases = [TestCase.model_validate(case) for case in test_cases]
        verified = TestVerificationResult.model_validate(verification)
        baseline = self._deterministic(cases, verified, stage3_payload)
        evaluation = baseline
        if self._client is not None:
            try:
                compact_payload = self._compact_llm_payload(
                    cases, verified, stage3_payload, baseline
                )
                full_size = len(json.dumps({
                    "test_cases": [
                        case.model_dump(mode="json") for case in cases
                    ],
                    "verification": verified.model_dump(mode="json"),
                    "code_understanding": stage3_payload,
                    "deterministic_baseline": baseline.model_dump(mode="json"),
                }, separators=(",", ":")).encode("utf-8"))
                user_prompt = json.dumps(
                    compact_payload, separators=(",", ":")
                )
                logger.info(
                    "Stage 6 evaluation prompt reduction before_bytes=%d "
                    "after_bytes=%d estimated_tokens=%d",
                    full_size, len(user_prompt.encode("utf-8")),
                    len(user_prompt.encode("utf-8")) // 4,
                )
                capacity_method = getattr(
                    type(self._client),
                    "generate_structured_capacity_aware",
                    None,
                )
                method = (
                    self._client.generate_structured_capacity_aware
                    if callable(capacity_method)
                    else self._client.generate_structured
                )
                response = method(
                    system_prompt=QUALITY_EVALUATION_SYSTEM_PROMPT,
                    user_prompt=user_prompt,
                    response_model=QualityEvaluation,
                )
                evaluation = QualityEvaluation.model_validate(response)
            except Exception as error:
                logger.warning(
                    "Stage 6 AI evaluation unavailable; using deterministic "
                    "baseline error=%s",
                    type(error).__name__,
                )
                evaluation = baseline
        dimensions = evaluation.dimension_scores.model_copy(update={
            "coverage": baseline.dimension_scores.coverage,
            "correctness": baseline.dimension_scores.correctness,
            "completeness": baseline.dimension_scores.completeness,
            "performance": 0.0,
        })
        overall_score = self._overall_score(dimensions)
        normalized = evaluation.model_copy(
            update={
                "overall_score": overall_score,
                "dimension_scores": dimensions,
                "feedback": baseline.feedback,
                "recommendations": [
                    item for item in baseline.recommendations
                    if "performance" not in item.casefold()
                ],
                "threshold_met": (
                    overall_score >= threshold
                    and dimensions.coverage >= threshold
                    and dimensions.completeness >= threshold
                ),
                "iteration": iteration,
            }
        )
        return normalized.model_copy(
            update={
                "regeneration_plan": self._build_regeneration_plan(
                    cases, verified, stage3_payload, normalized.overall_score, threshold
                )
            }
        )

    @staticmethod
    def _compact_llm_payload(
        cases: list[TestCase],
        verification: TestVerificationResult,
        stage3: dict[str, Any],
        baseline: QualityEvaluation,
    ) -> dict[str, Any]:
        weak_ids = {
            *baseline.feedback.improve_test_case_ids,
            *baseline.feedback.replace_test_case_ids,
        }
        compact_cases = [
            {
                "id": case.id,
                "title": case.title,
                "category": case.category.value,
                "expected_results": case.expected_results,
                "traceability": case.traceability,
            }
            for case in cases
            if case.id in weak_ids
        ]
        compact_results = [
            {
                "test_case_id": result.test_case_id,
                "status": result.status.value,
                "findings": [
                    {
                        "check": finding.check,
                        "status": finding.status.value,
                        "detail": finding.detail,
                    }
                    for finding in result.findings
                    if finding.status != VerificationStatus.VERIFIED
                ],
            }
            for result in verification.results
            if result.test_case_id in weak_ids
        ]
        symbols = {
            symbol
            for case in compact_cases
            for symbol in (
                (case.get("traceability") or {}).get("symbol"),
                *((case.get("traceability") or {}).get("symbols", [])),
            )
            if symbol
        }
        grounding = {
            "test_targets": [
                target for target in stage3.get("test_targets", [])
                if target.get("symbol") in symbols
            ],
            "api_endpoints": [
                endpoint for endpoint in stage3.get("api_endpoints", [])
                if endpoint.get("handler") in symbols
            ],
        }
        return {
            "suite_summary": {
                "total_tests": len(cases),
                "verification": verification.summary.model_dump(mode="json"),
            },
            "weak_test_cases": compact_cases,
            "failed_verification": compact_results,
            "relevant_grounding": grounding,
            "deterministic_baseline": baseline.model_dump(
                mode="json", exclude={"regeneration_plan"}
            ),
        }

    @staticmethod
    def _build_regeneration_plan(
        cases: list[TestCase],
        verification: TestVerificationResult,
        stage3_payload: dict[str, Any],
        score: float,
        threshold: float,
    ) -> RegenerationPlan:
        weak = [
            item.test_case_id
            for item in verification.results
            if item.status == VerificationStatus.PARTIAL
        ]
        failed = [
            item.test_case_id
            for item in verification.results
            if item.status == VerificationStatus.FAILED
        ]
        valid_categories = tuple(Category)
        present = {case.category.value for case in cases}
        missing = [item.value for item in valid_categories if item.value not in present]
        actions = [
            RegenerationAction(
                action=RegenerationActionType.ADD, category=category
            )
            for category in missing
        ]
        actions.extend(
            RegenerationAction(
                action=RegenerationActionType.UPDATE, test_case_id=case_id
            )
            for case_id in [*weak, *failed]
        )
        coverage_gaps = CoverageAnalyzer().completion_gaps(cases, stage3_payload)
        actions.extend(
            RegenerationAction(
                action=RegenerationActionType.ADD,
                category=gap["category"],
                target_symbol=gap["symbol"],
                coverage_requirement=gap["requirement"],
            )
            for gap in coverage_gaps
        )
        rationale = []
        if missing:
            rationale.append("Add tests for uncovered categories")
        if weak:
            rationale.append("Update partially verified test cases")
        if failed:
            rationale.append("Replace failed test cases")
        if coverage_gaps:
            rationale.append("Add tests for uncovered functions and branches")
        return RegenerationPlan(
            current_score=score,
            threshold=threshold,
            missing_categories=missing,
            weak_test_cases=weak,
            failed_test_cases=failed,
            actions=actions,
            rationale=rationale,
        )

    def _deterministic(
        self,
        cases: list[TestCase],
        verification: TestVerificationResult,
        stage3: dict[str, Any],
    ) -> QualityEvaluation:
        total = len(cases)
        checks = {item.test_case_id: item for item in verification.results}
        correctness = self._percentage(
            sum(
                self._proof_score(checks.get(case.id))
                for case in cases
            ),
            total,
        )
        traceability = self._percentage(
            sum(
                self._traceability_score(case, checks.get(case.id))
                for case in cases
            ),
            total,
        )
        coverage_analyzer = CoverageAnalyzer()
        coverage_summary = coverage_analyzer.analyze(cases, stage3)
        completeness = coverage_summary["completeness"]
        ids = Counter(case.id.casefold() for case in cases)
        semantic_keys = [
            Deduplicator._behavior_key(case) for case in cases
        ]
        unique_semantics = len({
            key for key in semantic_keys if key[0]
        }) + sum(not key[0] for key in semantic_keys)
        unique_ids = sum(count == 1 for count in ids.values())
        expectation_groups: dict[tuple[str, str, str], set[str]] = {}
        for symbol, category, branch, expected in semantic_keys:
            expectation_groups.setdefault(
                (symbol, category, branch), set()
            ).add(expected)
        contradictions = sum(
            max(0, len(expectations) - 1)
            for expectations in expectation_groups.values()
            if expectations
        )
        unsupported = sum(
            any(
                finding.status == VerificationStatus.FAILED
                and finding.check in {
                    "endpoint_behavior", "behavior_semantics",
                    "endpoint_exists", "symbol_exists", "file_exists",
                }
                for finding in result.findings
            )
            for result in verification.results
        )
        duplicates = self._percentage(
            max(
                0,
                min(unique_semantics, unique_ids)
                - contradictions - unsupported,
            ),
            total,
        )
        maintainability = self._percentage(
            sum(bool(case.title.strip()) and len(case.steps) <= 12 for case in cases),
            total,
        )
        category_coverage = self._percentage(
            len({case.category for case in cases}), len(tuple(Category))
        )
        category_scores = {
            category: 100.0 if any(case.category == category for case in cases) else 0.0
            for category in (
                Category.BOUNDARY,
                Category.NEGATIVE,
                Category.SECURITY,
            )
        }
        coverage = coverage_summary["target_coverage"]
        dimensions = QualityDimensionScores(
            coverage=coverage,
            correctness=correctness,
            traceability=traceability,
            completeness=completeness,
            duplicates=duplicates,
            maintainability=maintainability,
            category_coverage=category_coverage,
            boundary_coverage=category_scores[Category.BOUNDARY],
            negative_testing=category_scores[Category.NEGATIVE],
            security=category_scores[Category.SECURITY],
            performance=0.0,
            duplicate_quality=duplicates,
        )
        requested_scores = {
            "coverage": dimensions.coverage,
            "correctness": dimensions.correctness,
            "traceability": dimensions.traceability,
            "completeness": dimensions.completeness,
            "boundary_coverage": dimensions.boundary_coverage,
            "negative_testing": dimensions.negative_testing,
            "security": dimensions.security,
            "maintainability": dimensions.maintainability,
            "duplicate_quality": dimensions.duplicate_quality,
        }
        overall = round(sum(requested_scores.values()) / len(requested_scores), 2)
        partial = [
            item.test_case_id
            for item in verification.results
            if item.status == VerificationStatus.PARTIAL
        ]
        failed = [
            item.test_case_id
            for item in verification.results
            if item.status == VerificationStatus.FAILED
        ]
        present = {case.category.value for case in cases}
        missing = [
            category.value for category in Category if category.value not in present
        ]
        weak = [name for name, score in requested_scores.items() if score < 90]
        recommendations = [f"Improve {name.replace('_', ' ')}" for name in weak]
        return QualityEvaluation(
            overall_score=min(overall, coverage, completeness),
            dimension_scores=dimensions,
            recommendations=recommendations,
            feedback=QualityFeedback(
                weak_dimensions=weak,
                improve_test_case_ids=partial,
                replace_test_case_ids=failed,
                missing_categories=missing,
                instructions=recommendations,
            ),
            threshold_met=False,
            iteration=1,
        )

    @staticmethod
    def _percentage(value: float, total: int) -> float:
        return round((value / total) * 100, 2) if total else 0.0

    @staticmethod
    def _proof_score(result) -> float:
        if result is None or result.status == VerificationStatus.FAILED:
            return 0.0
        if result.status == VerificationStatus.PARTIAL:
            return 0.5
        deterministic = result.verification_path.value == "Rule-Based"
        located = any(
            item.symbol and item.line is not None for item in result.evidence
        )
        incorrect = any(
            finding.status == VerificationStatus.FAILED
            and finding.check in {
                "file_exists", "symbol_exists", "endpoint_exists",
                "symbol_file_alignment", "behavior_semantics",
                "endpoint_behavior",
            }
            for finding in result.findings
        )
        if incorrect:
            return 0.0
        if deterministic and located:
            return 1.0
        return 0.85 if result.evidence else 0.6

    @staticmethod
    def _traceability_score(case: TestCase, result) -> float:
        if not case.traceability:
            return 0.0
        if result is None:
            return 0.5
        incorrect = any(
            finding.status == VerificationStatus.FAILED
            and finding.check in {
                "file_exists", "symbol_exists", "endpoint_exists",
                "symbol_file_alignment",
            }
            for finding in result.findings
        )
        if incorrect:
            return 0.0
        return 1.0 if result.evidence else 0.5

    @staticmethod
    def _overall_score(dimensions: QualityDimensionScores) -> float:
        scores = [
            dimensions.coverage, dimensions.correctness, dimensions.traceability,
            dimensions.completeness, dimensions.boundary_coverage,
            dimensions.negative_testing, dimensions.security,
            dimensions.maintainability, dimensions.duplicate_quality,
        ]
        return min(
            round(sum(scores) / len(scores), 2),
            dimensions.coverage,
            dimensions.completeness,
        )
