"""Iterative Stage 4-6 quality improvement orchestration."""

import logging
import re
from collections.abc import Callable
from typing import Any

from app.agents.quality_evaluation.agent import TestQualityEvaluationAgent
from app.agents.semantic_verification.agent import TestVerificationAgent
from app.agents.test_generation.test_generation_agent import TestGenerationAgent
from app.agents.test_generation.deduplicator import Deduplicator
from app.schemas.test_case import TestCase, TestGenerationResult
from app.schemas.test_quality import (
    QualityEvaluation,
    QualityImprovementMetrics,
    QualityIterationSummary,
    QualityLoopResult,
    RegenerationAction,
    RegenerationActionType,
    RegenerationPlan,
)
from app.schemas.test_verification import (
    TestCaseVerification,
    TestVerificationResult,
    VerificationStatus,
    VerificationSummary,
)

logger = logging.getLogger(__name__)

MAX_QUALITY_ITERATIONS = 2
MAX_REGENERATION_BATCHES_PER_ITERATION = 2


class QualityLoopService:
    def __init__(
        self,
        generator: TestGenerationAgent,
        verifier: TestVerificationAgent,
        evaluator: TestQualityEvaluationAgent,
        *,
        threshold: float = 90,
        max_iterations: int = MAX_QUALITY_ITERATIONS,
        minimum_improvement_delta: float = 2,
        regeneration_batch_size: int = 12,
        regeneration_prompt_token_limit: int = 6_000,
        max_regeneration_batches_per_iteration: int = (
            MAX_REGENERATION_BATCHES_PER_ITERATION
        ),
    ) -> None:
        self._generator = generator
        self._verifier = verifier
        self._evaluator = evaluator
        self._threshold = threshold
        self._max_iterations = min(
            max(1, max_iterations), MAX_QUALITY_ITERATIONS
        )
        self._minimum_improvement_delta = minimum_improvement_delta
        self._regeneration_batch_size = max(1, regeneration_batch_size)
        self._regeneration_prompt_token_limit = max(
            1_000, regeneration_prompt_token_limit
        )
        self._max_regeneration_batches_per_iteration = max(
            1, max_regeneration_batches_per_iteration
        )

    def cache_fingerprint(self) -> dict[str, Any]:
        """Return all stable quality-loop and regeneration policy settings.

        Returns:
            JSON-compatible optimization, model, threshold, and iteration policy.
        """
        return {
            "threshold": self._threshold,
            "max_iterations": self._max_iterations,
            "minimum_improvement_delta": self._minimum_improvement_delta,
            "regeneration_batch_size": self._regeneration_batch_size,
            "regeneration_prompt_token_limit": (
                self._regeneration_prompt_token_limit
            ),
            "max_regeneration_batches_per_iteration": (
                self._max_regeneration_batches_per_iteration
            ),
            "regeneration_policy": "quality-ranked-non-destructive-merge-v2",
            "generator": self._generator.cache_fingerprint(),
            "verifier": self._verifier.cache_fingerprint(),
            "evaluator": self._evaluator.cache_fingerprint(),
        }

    def run(
        self,
        stage3_payload: dict[str, Any],
        source_files: list[dict[str, Any]],
        initial_generation: dict[str, Any] | None = None,
        initial_verification: dict[str, Any] | TestVerificationResult | None = None,
        resume_state: dict[str, Any] | None = None,
        checkpoint: Callable[[str, dict[str, Any]], None] | None = None,
        repo_root: str | None = None,
    ) -> QualityLoopResult:
        resume_state = resume_state or {}
        generation = (
            resume_state.get("generation")
            or initial_generation
            or self._generator.generate(stage3_payload)
        )
        initial_verification = resume_state.get("verification") or initial_verification
        start_iteration = max(1, int(resume_state.get("next_iteration", 1)))
        logger.info(
            "Quality optimization resume resume_point=%s iteration=%d",
            resume_state.get("resume_point", "start"), start_iteration,
        )
        cases = [
            TestCase.model_validate(item) for item in generation["generated_test_cases"]
        ]
        history = []
        summaries = []
        regeneration_plans = []
        stopping_reason = "max_iterations"
        preserved_count = 0
        regenerated_count = 0
        executed_regeneration_batches = 0
        regeneration_batch_limit_reached = False
        previous_score: float | None = None
        pending_verification: dict[str, Any] | None = None
        best_score = float("-inf")
        best_suite: list[TestCase] = []
        best_generation: TestGenerationResult | None = None
        best_verification: TestVerificationResult | None = None
        best_evaluation = None
        if all(
            key in resume_state
            for key in (
                "best_score", "best_suite", "best_generation",
                "best_verification", "best_evaluation",
            )
        ):
            best_score = float(resume_state["best_score"])
            best_suite = [
                TestCase.model_validate(item)
                for item in resume_state["best_suite"]
            ]
            best_generation = TestGenerationResult.model_validate(
                resume_state["best_generation"]
            )
            best_verification = TestVerificationResult.model_validate(
                resume_state["best_verification"]
            )
            best_evaluation = self._evaluator_result(
                resume_state["best_evaluation"]
            )
        attempted_actions: set[tuple[str, str | None, str | None, str | None]] = set()
        for iteration in range(start_iteration, self._max_iterations + 1):
            if iteration == start_iteration and initial_verification is not None:
                verification = TestVerificationResult.model_validate(
                    initial_verification
                ).model_dump(mode="json")
            elif pending_verification is not None:
                verification = pending_verification
                pending_verification = None
            else:
                verification = self._verifier.verify(cases, stage3_payload, source_files, repo_root=repo_root)
            if checkpoint is not None:
                checkpoint_payload = {
                    "generation": generation,
                    "verification": verification,
                    "next_iteration": iteration,
                    "resume_point": "evaluation",
                    "processing_status": "in_progress",
                }
                if best_generation is not None:
                    checkpoint_payload.update(self._best_checkpoint(
                        best_score, best_suite, best_generation,
                        best_verification, best_evaluation,
                    ))
                checkpoint("verification", checkpoint_payload)
            evaluation = self._evaluator.evaluate(
                cases,
                verification,
                stage3_payload,
                threshold=self._threshold,
                iteration=iteration,
            )
            history.append(evaluation)
            current_generation = TestGenerationResult.model_validate({
                **generation,
                "generated_test_cases": [
                    case.model_dump(mode="json") for case in cases
                ],
                "total_after_deduplication": len(cases),
            })
            current_verification = TestVerificationResult.model_validate(
                verification
            )
            if evaluation.overall_score > best_score:
                best_score = evaluation.overall_score
                best_suite = [
                    case.model_copy(deep=True) for case in cases
                ]
                best_generation = current_generation.model_copy(deep=True)
                best_verification = current_verification.model_copy(deep=True)
                best_evaluation = evaluation.model_copy(deep=True)
                if checkpoint is not None:
                    checkpoint("best_suite", {
                        "generation": current_generation.model_dump(mode="json"),
                        "verification": current_verification.model_dump(mode="json"),
                        "next_iteration": iteration,
                        "resume_point": "evaluation",
                        "processing_status": "in_progress",
                        **self._best_checkpoint(
                            best_score,
                            best_suite,
                            best_generation,
                            best_verification,
                            best_evaluation,
                        ),
                    })
            improvement_delta = (
                0.0
                if previous_score is None
                else round(evaluation.overall_score - previous_score, 2)
            )
            summary = TestVerificationResult.model_validate(verification).summary
            summaries.append(
                QualityIterationSummary(
                    iteration=iteration,
                    overall_score=evaluation.overall_score,
                    verified=summary.verified,
                    partial=summary.partial,
                    failed=summary.failed,
                    preserved=preserved_count,
                    regenerated=regenerated_count,
                    threshold_met=evaluation.threshold_met,
                )
            )
            status_by_id = {
                item["test_case_id"]: item["status"] for item in verification["results"]
            }
            preserved = [
                case
                for case in cases
                if status_by_id.get(case.id) == VerificationStatus.VERIFIED
            ]
            weak = [case for case in cases if case not in preserved]
            plan = evaluation.regeneration_plan or self._legacy_plan(
                evaluation, weak
            )
            remaining_actions = [
                action
                for action in plan.actions
                if self._action_key(action) not in attempted_actions
            ]
            remaining_categories = [
                action.category
                for action in remaining_actions
                if action.action == RegenerationActionType.ADD
                and action.category is not None
            ]
            remaining_ids = {
                action.test_case_id
                for action in remaining_actions
                if action.action == RegenerationActionType.UPDATE
            }
            actionable_plan = plan.model_copy(
                update={
                    "missing_categories": remaining_categories,
                    "weak_test_cases": [
                        item for item in plan.weak_test_cases if item in remaining_ids
                    ],
                    "failed_test_cases": [
                        item for item in plan.failed_test_cases if item in remaining_ids
                    ],
                    "actions": remaining_actions,
                }
            )
            regeneration_plans.append(actionable_plan)
            regeneration_requested = False
            iteration_stopping_reason: str | None = None
            coverage_unmet = evaluation.dimension_scores.coverage < self._threshold
            if evaluation.threshold_met:
                iteration_stopping_reason = "threshold_met"
            elif iteration == self._max_iterations:
                iteration_stopping_reason = "max_iterations"
            elif not remaining_actions:
                iteration_stopping_reason = "no_further_gaps_identifiable"
            elif (
                previous_score is not None
                and improvement_delta < self._minimum_improvement_delta
                and not coverage_unmet
            ):
                iteration_stopping_reason = "no_improvements"
            else:
                regeneration_requested = True
            logger.info(
                "Quality optimization iteration=%d previous_score=%s "
                "current_score=%.2f coverage=%.2f threshold=%.2f improvement_delta=%.2f "
                "remaining_weak_categories=%s regeneration_requested=%s "
                "stopping_reason=%s",
                iteration,
                previous_score,
                evaluation.overall_score,
                evaluation.dimension_scores.coverage,
                self._threshold,
                improvement_delta,
                remaining_categories,
                regeneration_requested,
                iteration_stopping_reason,
            )
            if iteration_stopping_reason is not None:
                stopping_reason = iteration_stopping_reason
                break
            previous_score = evaluation.overall_score
            feedback_payload = dict(stage3_payload)
            feedback_payload["regeneration_plan"] = actionable_plan.model_dump(
                mode="json"
            )
            feedback_payload["existing_test_case_count"] = len(cases)
            feedback_payload["requested_regenerated_count"] = len(
                remaining_actions
            )
            feedback_payload["test_cases_to_improve"] = [
                case.model_dump(mode="json") for case in weak
            ]
            feedback_payload["regeneration_verification"] = verification
            (
                improved,
                executed_batches,
                batch_limit_reached,
                executed_actions,
            ) = self._generate_regeneration_batches(
                feedback_payload, actionable_plan,
                checkpoint=checkpoint, next_iteration=iteration + 1,
                preserved_cases=cases,
                best_checkpoint=self._best_checkpoint(
                    best_score, best_suite, best_generation,
                    best_verification, best_evaluation,
                ),
            )
            executed_regeneration_batches += executed_batches
            regeneration_batch_limit_reached |= batch_limit_reached
            attempted_actions.update(
                self._action_key(action) for action in executed_actions
            )
            replacements = [
                TestCase.model_validate(item)
                for item in improved["generated_test_cases"]
            ]
            if not replacements:
                stopping_reason = (
                    "provider_exhausted"
                    if (improved.get("generation_reason") or "").startswith("all_providers")
                    else "regeneration_batch_limit"
                    if batch_limit_reached
                    else "no_improvements"
                )
                break
            replacement_verification = self._verifier.verify(
                replacements,
                stage3_payload,
                source_files,
                repo_root=repo_root,
            )
            cases, pending_verification, regenerated_count = (
                self._merge_regenerated(
                    cases,
                    verification,
                    replacements,
                    replacement_verification,
                    executed_actions,
                )
            )
            preserved_count = len(cases) - regenerated_count
            generation = {
                **improved,
                "generated_test_cases": [
                    case.model_dump(mode="json") for case in cases
                ],
                "total_after_deduplication": len(cases),
            }
            if checkpoint is not None:
                checkpoint("generation", {
                    "generation": generation,
                    "verification": None,
                    "next_iteration": iteration + 1,
                    "resume_point": "verification",
                    "processing_status": "in_progress",
                    **self._best_checkpoint(
                        best_score, best_suite, best_generation,
                        best_verification, best_evaluation,
                    ),
                })
        if (
            best_generation is None
            or best_verification is None
            or best_evaluation is None
        ):
            raise RuntimeError("Quality optimization produced no evaluated suite")
        final_generation = best_generation
        final_verification = best_verification
        evaluation = best_evaluation
        final_generation, final_verification = self._finalize_verified_suite(
            final_generation, final_verification
        )
        initial_evaluation = history[0]
        optimization_limit_reached = (
            stopping_reason == "max_iterations"
            or regeneration_batch_limit_reached
        )
        logger.info(
            "Quality optimization exit final_exit_reason=%s iterations=%d",
            stopping_reason, iteration,
        )
        logger.info(
            "\n===== QUALITY OPTIMIZATION SUMMARY =====\n"
            "Iterations Performed: %d\n"
            "Configured Limit: %d\n"
            "Regeneration Batches Executed: %d\n"
            "Configured Batch Limit: %d\n"
            "Initial Score: %.2f\n"
            "Final Score: %.2f\n"
            "Threshold: %.2f\n"
            "Stop Reason: %s\n"
            "Optimization Limit Reached: %s",
            iteration,
            self._max_iterations,
            executed_regeneration_batches,
            self._max_regeneration_batches_per_iteration,
            initial_evaluation.overall_score,
            best_score,
            self._threshold,
            stopping_reason,
            optimization_limit_reached,
        )
        return QualityLoopResult(
            test_generation=final_generation,
            test_verification=final_verification,
            quality_evaluation=evaluation,
            iterations=iteration,
            optimized_test_cases=final_generation.generated_test_cases,
            evaluation_history=history,
            iteration_summaries=summaries,
            improvement_metrics=QualityImprovementMetrics(
                initial_score=initial_evaluation.overall_score,
                final_score=best_score,
                score_delta=round(
                    best_score - initial_evaluation.overall_score, 2
                ),
                initial_verified=summaries[0].verified,
                final_verified=final_verification.summary.verified,
                verified_delta=final_verification.summary.verified
                - summaries[0].verified,
            ),
            stopping_reason=stopping_reason,
            initial_score=initial_evaluation.overall_score,
            final_score=best_score,
            regeneration_plans=regeneration_plans,
            optimized_test_suite=final_generation.generated_test_cases,
            processing_status=(
                "partial_success" if stopping_reason == "provider_exhausted" else "completed"
            ),
            resume_point=(
                "quality_optimization" if stopping_reason == "provider_exhausted" else None
            ),
            final_exit_reason=stopping_reason,
            optimization_limit_reached=optimization_limit_reached,
            iterations_performed=iteration,
            configured_iteration_limit=self._max_iterations,
            executed_regeneration_batches=executed_regeneration_batches,
            configured_regeneration_batch_limit=(
                self._max_regeneration_batches_per_iteration
            ),
            final_quality_score=best_score,
            stop_reason=stopping_reason,
        )

    def _generate_regeneration_batches(
        self,
        payload: dict[str, Any],
        plan: RegenerationPlan,
        *,
        checkpoint: Callable[[str, dict[str, Any]], None] | None = None,
        next_iteration: int,
        preserved_cases: list[TestCase],
        best_checkpoint: dict[str, Any] | None = None,
    ) -> tuple[
        dict[str, Any], int, bool, list[RegenerationAction]
    ]:
        actions = list(plan.actions)
        count_batches = [
            actions[index:index + self._regeneration_batch_size]
            for index in range(0, len(actions), self._regeneration_batch_size)
        ] or [[]]
        batches = [
            sized
            for batch in count_batches
            for sized in self._prompt_sized_batches(payload, plan, batch)
        ] or [[]]
        generated: list[dict[str, Any]] = []
        total = 0
        reason = None
        scheduled_batches = batches[
            :self._max_regeneration_batches_per_iteration
        ]
        batch_limit_reached = len(batches) > len(scheduled_batches)
        executed_actions: list[RegenerationAction] = []
        if batch_limit_reached:
            logger.warning(
                "Quality regeneration batch limit reached scheduled=%d "
                "remaining_batches=%d configured_limit=%d",
                len(scheduled_batches),
                len(batches) - len(scheduled_batches),
                self._max_regeneration_batches_per_iteration,
            )
        executed_batches = 0
        for index, actions_batch in enumerate(scheduled_batches, start=1):
            batch_plan = plan.model_copy(update={"actions": actions_batch})
            batch_payload = {
                **payload,
                "regeneration_plan": batch_plan.model_dump(mode="json"),
                "requested_regenerated_count": len(actions_batch),
            }
            logger.info(
                "Quality regeneration batch=%d/%d uncovered_requirements=%d",
                index, len(batches), len(actions_batch),
            )
            result = self._generator.generate(batch_payload)
            executed_batches += 1
            executed_actions.extend(actions_batch)
            generated.extend(result["generated_test_cases"])
            total += result["total_generated"]
            reason = reason or result.get("generation_reason")
            if checkpoint is not None and result["generated_test_cases"]:
                partial_cases = self._deduplicate(
                    [
                        *preserved_cases,
                        *[TestCase.model_validate(item) for item in generated],
                    ]
                )
                checkpoint("generation_batch", {
                    "generation": {
                        "generated_test_cases": [
                            item.model_dump(mode="json") for item in partial_cases
                        ],
                        "coverage_summary": {},
                        "total_generated": total,
                        "total_after_deduplication": len(partial_cases),
                        "generation_status": "partial_coverage_incomplete",
                        "uncovered_requirements": [],
                    },
                    "verification": None,
                    "next_iteration": next_iteration,
                    "resume_point": f"generation_batch_{index + 1}",
                    "processing_status": "in_progress",
                    **(best_checkpoint or {}),
                })
            if reason and not result["generated_test_cases"]:
                break
        cases = self._deduplicate(
            [TestCase.model_validate(item) for item in generated]
        )
        return (
            {
                "generated_test_cases": [
                    item.model_dump(mode="json") for item in cases
                ],
                "coverage_summary": {},
                "total_generated": total,
                "total_after_deduplication": len(cases),
                "generation_status": (
                    "partial_coverage_incomplete"
                    if reason or batch_limit_reached
                    else "complete"
                ),
                "generation_reason": reason,
                "uncovered_requirements": [],
            },
            executed_batches,
            batch_limit_reached,
            executed_actions,
        )

    def _prompt_sized_batches(
        self,
        payload: dict[str, Any],
        plan: RegenerationPlan,
        actions: list[RegenerationAction],
    ) -> list[list[RegenerationAction]]:
        estimator = getattr(
            self._generator, "estimate_regeneration_prompt_tokens", None
        )
        if not callable(estimator) or not actions:
            return [actions]
        batches: list[list[RegenerationAction]] = []
        current: list[RegenerationAction] = []
        for action in actions:
            candidate = [*current, action]
            candidate_plan = plan.model_copy(update={"actions": candidate})
            candidate_payload = {
                **payload,
                "regeneration_plan": candidate_plan.model_dump(mode="json"),
                "requested_regenerated_count": len(candidate),
            }
            estimate = estimator(candidate_payload)
            if (
                isinstance(estimate, int)
                and estimate > self._regeneration_prompt_token_limit
                and current
            ):
                batches.append(current)
                current = [action]
            else:
                current = candidate
        if current:
            batches.append(current)
        if len(batches) > 1:
            logger.info(
                "Stage 6 prompt-aware batching actions=%d batches=%d "
                "prompt_token_limit=%d",
                len(actions), len(batches),
                self._regeneration_prompt_token_limit,
            )
        return batches

    @staticmethod
    def _evaluator_result(value: Any) -> QualityEvaluation:
        return QualityEvaluation.model_validate(value)

    @staticmethod
    def _best_checkpoint(
        score: float,
        suite: list[TestCase],
        generation: TestGenerationResult | None,
        verification: TestVerificationResult | None,
        evaluation: QualityEvaluation | None,
    ) -> dict[str, Any]:
        if generation is None or verification is None or evaluation is None:
            return {}
        return {
            "best_score": score,
            "best_suite": [
                case.model_dump(mode="json") for case in suite
            ],
            "best_generation": generation.model_dump(mode="json"),
            "best_verification": verification.model_dump(mode="json"),
            "best_evaluation": evaluation.model_dump(mode="json"),
        }

    @classmethod
    def _merge_regenerated(
        cls,
        existing_cases: list[TestCase],
        existing_verification: dict[str, Any] | TestVerificationResult,
        regenerated_cases: list[TestCase],
        regenerated_verification: dict[str, Any] | TestVerificationResult,
        executed_actions: list[RegenerationAction],
    ) -> tuple[list[TestCase], dict[str, Any], int]:
        existing_result = TestVerificationResult.model_validate(
            existing_verification
        )
        regenerated_result = TestVerificationResult.model_validate(
            regenerated_verification
        )
        old_checks = {
            item.test_case_id: item for item in existing_result.results
        }
        new_checks = {
            item.test_case_id: item for item in regenerated_result.results
        }
        update_ids = {
            action.test_case_id
            for action in executed_actions
            if action.action == RegenerationActionType.UPDATE
            and action.test_case_id is not None
        }
        existing_ids = {case.id for case in existing_cases}
        accepted_updates: dict[str, TestCase] = {}
        accepted_additions: list[TestCase] = []

        for raw_case in regenerated_cases:
            case = cls._normalize_repaired_case(raw_case)
            candidate_check = new_checks.get(case.id)
            if candidate_check is None:
                continue
            comparable_candidate = cls._without_duplicate_finding(
                candidate_check
            )
            existing_check = old_checks.get(case.id)
            if case.id in update_ids and existing_check is not None:
                if cls._verification_strength(
                    comparable_candidate
                ) > cls._verification_strength(
                    cls._without_duplicate_finding(existing_check)
                ):
                    accepted_updates[case.id] = case
            elif (
                case.id not in existing_ids
                and comparable_candidate.status != VerificationStatus.FAILED
            ):
                accepted_additions.append(case)

        candidates: list[tuple[TestCase, TestCaseVerification, bool]] = []
        for original in existing_cases:
            case = accepted_updates.get(original.id, original)
            check = (
                new_checks.get(case.id)
                if original.id in accepted_updates
                else old_checks.get(original.id)
            )
            if check is not None:
                candidates.append((
                    case, cls._without_duplicate_finding(check),
                    original.id in accepted_updates,
                ))
        candidates.extend(
            (case, cls._without_duplicate_finding(new_checks[case.id]), True)
            for case in accepted_additions if case.id in new_checks
        )
        selected: list[tuple[TestCase, TestCaseVerification, bool]] = []
        for candidate in candidates:
            case, check, _ = candidate
            duplicate_index = next(
                (
                    index for index, (chosen, _, _) in enumerate(selected)
                    if chosen.id.casefold() == case.id.casefold()
                    or (
                        bool(Deduplicator._behavior_key(case)[0])
                        and Deduplicator._behavior_key(chosen)
                        == Deduplicator._behavior_key(case)
                    )
                ),
                None,
            )
            if duplicate_index is None:
                selected.append(candidate)
                continue
            if cls._verification_strength(check) > cls._verification_strength(
                selected[duplicate_index][1]
            ):
                selected[duplicate_index] = candidate
        supported = [
            item for item in selected
            if not cls._has_impossible_expectation(item[1])
        ]
        selected = []
        for candidate in supported:
            case, check, _ = candidate
            key = cls._contradiction_key(case)
            conflict_index = next(
                (
                    index for index, (chosen, _, _) in enumerate(selected)
                    if cls._contradiction_key(chosen) == key
                    and Deduplicator._behavior_key(chosen)[3]
                    != Deduplicator._behavior_key(case)[3]
                ),
                None,
            )
            if conflict_index is None:
                selected.append(candidate)
            elif cls._verification_strength(check) > cls._verification_strength(
                selected[conflict_index][1]
            ):
                selected[conflict_index] = candidate
        merged = [case for case, _, _ in selected]
        selected_checks = [check for _, check, _ in selected]
        counts = {
            status: sum(item.status == status for item in selected_checks)
            for status in VerificationStatus
        }
        combined = TestVerificationResult(
            results=selected_checks,
            summary=VerificationSummary(
                verified=counts[VerificationStatus.VERIFIED],
                partial=counts[VerificationStatus.PARTIAL],
                failed=counts[VerificationStatus.FAILED],
            ),
            total_verified=counts[VerificationStatus.VERIFIED],
        )
        accepted_count = sum(is_new for _, _, is_new in selected)
        return merged, combined.model_dump(mode="json"), accepted_count

    @staticmethod
    def _verification_strength(
        result: TestCaseVerification,
    ) -> tuple[int, int, int, float]:
        ranks = {
            VerificationStatus.FAILED: 0,
            VerificationStatus.PARTIAL: 1,
            VerificationStatus.VERIFIED: 2,
        }
        deterministic = int(
            result.verification_path.value == "Rule-Based"
            and any(
                finding.status == VerificationStatus.VERIFIED
                for finding in result.findings
            )
        )
        correct_evidence = sum(
            item.line is not None and bool(item.symbol)
            for item in result.evidence
        )
        return ranks[result.status], deterministic, correct_evidence, result.confidence

    @staticmethod
    def _normalize_repaired_case(case: TestCase) -> TestCase:
        title = re.sub(
            r"(?i)(?:\s*[-:]\s*(?:repair(?:ed)?|regenerated))+$",
            " - Repaired",
            case.title.strip(),
        )
        title = re.sub(
            r"(?i)\b(not)(?:[-\s]+\1)+\b", r"\1", title
        )
        title = re.sub(
            r"(?i)\b(repair(?:ed)?)(?:\s+\1)+\b", r"\1", title
        )
        return case.model_copy(update={"title": " ".join(title.split())})

    @staticmethod
    def _without_duplicate_finding(
        result: TestCaseVerification,
    ) -> TestCaseVerification:
        findings = [
            item for item in result.findings if item.check != "duplicate"
        ]
        if len(findings) == len(result.findings):
            return result
        if not findings:
            status = VerificationStatus.PARTIAL
        elif any(item.status == VerificationStatus.FAILED for item in findings):
            status = VerificationStatus.FAILED
        elif any(item.status == VerificationStatus.PARTIAL for item in findings):
            status = VerificationStatus.PARTIAL
        else:
            status = VerificationStatus.VERIFIED
        return result.model_copy(update={"findings": findings, "status": status})

    @staticmethod
    def _has_impossible_expectation(result: TestCaseVerification) -> bool:
        return any(
            finding.status == VerificationStatus.FAILED
            and finding.check in {
                "endpoint_behavior", "behavior_semantics",
                "endpoint_exists", "symbol_exists", "file_exists",
            }
            for finding in result.findings
        )

    @staticmethod
    def _contradiction_key(case: TestCase) -> tuple[str, str, str]:
        symbol, category, branch, _ = Deduplicator._behavior_key(case)
        return symbol, category, branch

    def _legacy_plan(self, evaluation, weak: list[TestCase]) -> RegenerationPlan:
        """Support injected evaluators that predate deterministic plans."""
        weak_ids = [case.id for case in weak]
        failed = set(evaluation.feedback.replace_test_case_ids)
        return RegenerationPlan(
            current_score=evaluation.overall_score,
            threshold=self._threshold,
            missing_categories=evaluation.feedback.missing_categories,
            weak_test_cases=[item for item in weak_ids if item not in failed],
            failed_test_cases=[item for item in weak_ids if item in failed],
            actions=[
                *[
                    RegenerationAction(
                        action=RegenerationActionType.ADD, category=category
                    )
                    for category in evaluation.feedback.missing_categories
                ],
                *[
                    RegenerationAction(
                        action=RegenerationActionType.UPDATE, test_case_id=case_id
                    )
                    for case_id in weak_ids
                ],
            ],
            rationale=[],
        )

    @staticmethod
    def _action_key(action: RegenerationAction) -> tuple[str, str | None, str | None, str | None]:
        return (
            action.action.value,
            action.test_case_id or action.target_symbol,
            action.coverage_requirement,
            action.category,
        )

    @staticmethod
    def _deduplicate(cases: list[TestCase]) -> list[TestCase]:
        normalized = [
            QualityLoopService._normalize_repaired_case(case) for case in cases
        ]
        semantic_unique = Deduplicator().deduplicate(normalized)
        result = []
        seen_ids, seen_titles, seen_steps = set(), set(), set()
        for case in semantic_unique:
            title = " ".join(case.title.casefold().split())
            steps = tuple(" ".join(item.casefold().split()) for item in case.steps)
            if case.id in seen_ids or title in seen_titles or steps in seen_steps:
                continue
            seen_ids.add(case.id)
            seen_titles.add(title)
            seen_steps.add(steps)
            result.append(case)
        return result

    @classmethod
    def _finalize_verified_suite(
        cls,
        generation: TestGenerationResult,
        verification: TestVerificationResult,
    ) -> tuple[TestGenerationResult, TestVerificationResult]:
        """Enforce final-suite uniqueness and deterministic support."""
        checks = {item.test_case_id: item for item in verification.results}
        eligible: list[tuple[TestCase, TestCaseVerification]] = []
        for case in generation.generated_test_cases:
            check = checks.get(case.id)
            if (
                check is None
                or check.status != VerificationStatus.VERIFIED
                or cls._has_impossible_expectation(check)
                or any(item.check == "duplicate" for item in check.findings)
            ):
                continue
            eligible.append((case, check))

        selected: dict[tuple[str, str, str], tuple[TestCase, TestCaseVerification]] = {}
        order: list[tuple[str, str, str]] = []
        for case, check in eligible:
            key = Deduplicator._scenario_key(case)
            current = selected.get(key)
            if current is None:
                selected[key] = (case, check)
                order.append(key)
            elif cls._verification_strength(check) > cls._verification_strength(
                current[1]
            ):
                selected[key] = (case, check)

        final_pairs = [selected[key] for key in order]
        cases = cls._deduplicate([case for case, _ in final_pairs])
        allowed_ids = {case.id for case in cases}
        results = [
            check for case, check in final_pairs if case.id in allowed_ids
        ]
        summary = VerificationSummary(
            verified=len(results), partial=0, failed=0
        )
        return (
            generation.model_copy(update={
                "generated_test_cases": cases,
                "total_after_deduplication": len(cases),
            }),
            verification.model_copy(update={
                "results": results,
                "summary": summary,
                "total_verified": len(results),
            }),
        )
