from unittest.mock import Mock

from app.schemas.test_quality import (
    QualityEvaluation,
    RegenerationAction,
    RegenerationPlan,
)
from app.services.quality_loop_service import QualityLoopService
from app.schemas import test_case as test_case_schema
from app.schemas import test_verification as verification_schema


def _case(case_id, title):
    return {
        "id": case_id,
        "title": title,
        "description": title,
        "category": "functional",
        "priority": "medium",
        "severity": "minor",
        "steps": [title],
        "expected_results": [f"{title} succeeds"],
    }


def _generation(cases):
    return {
        "generated_test_cases": cases,
        "coverage_summary": {
            "requirement_coverage": 0.0,
            "category_coverage": 10.0,
        },
        "total_generated": len(cases),
        "total_after_deduplication": len(cases),
    }


def _verification(statuses):
    results = [
        {
            "test_case_id": case_id,
            "status": status,
            "confidence": 0.9,
            "evidence": [],
            "findings": [],
        }
        for case_id, status in statuses.items()
    ]
    return {
        "results": results,
        "summary": {
            "verified": list(statuses.values()).count("Verified"),
            "partial": list(statuses.values()).count("Partial"),
            "failed": list(statuses.values()).count("Failed"),
        },
        "total_verified": list(statuses.values()).count("Verified"),
    }


def _evaluation(score, iteration, improve=None, replace=None, missing=None):
    return QualityEvaluation.model_validate(
        {
            "overall_score": score,
            "dimension_scores": {
                "coverage": score,
                "correctness": score,
                "traceability": score,
                "completeness": score,
                "duplicates": score,
                "maintainability": score,
                "category_coverage": score,
            },
            "recommendations": ["Improve weak tests"] if score < 90 else [],
            "feedback": {
                "weak_dimensions": ["correctness"] if score < 90 else [],
                "improve_test_case_ids": improve or [],
                "replace_test_case_ids": replace or [],
                "missing_categories": missing or [],
                "instructions": ["Improve weak tests"] if score < 90 else [],
            },
            "threshold_met": score >= 90,
            "iteration": iteration,
        }
    )


def test_repaired_name_normalization_removes_repeated_suffixes() -> None:
    payload = _case("TC-1", "Reject not-not-user - Repaired - Repaired")
    normalized = QualityLoopService._normalize_repaired_case(
        test_case_schema.TestCase.model_validate(payload)
    )

    assert normalized.title == "Reject not-user - Repaired"


def test_merge_keeps_strongest_semantic_variant_and_removes_duplicate_ids() -> None:
    original_payload = _case("TC-1", "Reject missing receiver")
    original_payload["traceability"] = {"symbol": "transfer"}
    repaired_payload = _case("TC-2", "Unknown recipient - Repaired")
    repaired_payload["description"] = "transfer to missing receiver"
    repaired_payload["steps"] = ["Transfer to a missing receiver"]
    repaired_payload["expected_results"] = ["Raises KeyError"]
    repaired_payload["traceability"] = {"symbol": "transfer"}
    original_payload["description"] = "transfer to missing receiver"
    original_payload["steps"] = ["Transfer to a missing receiver"]
    original_payload["expected_results"] = ["Raises KeyError"]
    existing = _verification({"TC-1": "Partial"})
    regenerated = _verification({"TC-2": "Verified"})
    regenerated["results"][0]["evidence"] = [{
        "file": "bank.py", "symbol": "transfer", "line": 10,
        "detail": "Deterministic KeyError path",
    }]

    merged, verification, _ = QualityLoopService._merge_regenerated(
        [test_case_schema.TestCase.model_validate(original_payload)],
        existing,
        [test_case_schema.TestCase.model_validate(repaired_payload)],
        regenerated,
        [],
    )

    assert [item.id for item in merged] == ["TC-2"]
    assert verification["summary"]["verified"] == 1


def test_merge_filters_unsupported_endpoint_expectation() -> None:
    payload = _case("TC-BAD", "Endpoint returns HTTP 100")
    payload["traceability"] = {"symbol": "create_account", "route": "/accounts"}
    verification = {
        "results": [{
            "test_case_id": "TC-BAD", "status": "Failed",
            "confidence": 0.95, "evidence": [],
            "findings": [{
                "check": "endpoint_behavior", "status": "Failed",
                "detail": "HTTP 100 is unsupported", "evidence": [],
            }],
        }],
        "summary": {"verified": 0, "partial": 0, "failed": 1},
        "total_verified": 0,
    }

    merged, combined, _ = QualityLoopService._merge_regenerated(
        [test_case_schema.TestCase.model_validate(payload)], verification, [], _verification({}), []
    )

    assert merged == []
    assert combined["results"] == []


def test_merge_removes_contradictory_scenario_expectations() -> None:
    first = _case("TC-TRUE", "Verify password")
    second = _case("TC-FALSE", "Verify password")
    for payload in (first, second):
        payload["description"] = "verify_password with matching credentials"
        payload["steps"] = ["Call verify_password with matching credentials"]
        payload["traceability"] = {"symbol": "verify_password"}
    first["expected_results"] = ["Returns true"]
    second["expected_results"] = ["Returns false"]
    existing = _verification({"TC-TRUE": "Verified"})
    regenerated = _verification({"TC-FALSE": "Verified"})
    regenerated["results"][0]["confidence"] = 0.8

    merged, _, _ = QualityLoopService._merge_regenerated(
        [test_case_schema.TestCase.model_validate(first)],
        existing,
        [test_case_schema.TestCase.model_validate(second)],
        regenerated,
        [],
    )

    assert [item.id for item in merged] == ["TC-TRUE"]


def test_final_suite_contains_only_unique_verified_supported_scenarios() -> None:
    first = _case("TC-1", "Correct password")
    duplicate = _case("TC-2", "Matching credentials")
    weak = _case("TC-3", "Invented authentication rule")
    for payload in (first, duplicate):
        payload["description"] = "login with matching credentials"
        payload["steps"] = ["Call login with the correct password"]
        payload["expected_results"] = ["Returns true"]
        payload["traceability"] = {
            "symbol": "login", "route": "/login", "method": "POST",
        }
    weak["traceability"] = {"symbol": "login"}

    final_generation, final_verification = (
        QualityLoopService._finalize_verified_suite(
            test_case_schema.TestGenerationResult.model_validate(
                _generation([first, duplicate, weak])
            ),
            verification_schema.TestVerificationResult.model_validate(
                _verification({
                    "TC-1": "Verified",
                    "TC-2": "Verified",
                    "TC-3": "Partial",
                })
            ),
        )
    )

    assert [item.id for item in final_generation.generated_test_cases] == ["TC-1"]
    assert [item.test_case_id for item in final_verification.results] == ["TC-1"]


def test_loop_preserves_verified_and_regenerates_only_weak_cases() -> None:
    initial = [
        _case("TC-1", "Verified case"),
        _case("TC-2", "Partial case"),
        _case("TC-3", "Failed case"),
    ]
    replacements = [
        _case("TC-2", "Improved partial"),
        _case("TC-4", "Replacement failed"),
    ]
    generator, verifier, evaluator = Mock(), Mock(), Mock()
    generator.generate.return_value = _generation(replacements)
    verifier.verify.side_effect = [
        _verification({"TC-1": "Verified", "TC-2": "Partial", "TC-3": "Failed"}),
        _verification({"TC-1": "Verified", "TC-2": "Verified", "TC-4": "Verified"}),
    ]
    evaluator.evaluate.side_effect = [
        _evaluation(70, 1, ["TC-2"], ["TC-3"]),
        _evaluation(95, 2),
    ]
    service = QualityLoopService(
        generator, verifier, evaluator, threshold=90, max_iterations=3
    )

    result = service.run({}, [], _generation(initial))

    assert result.iterations == 2
    assert result.quality_evaluation.overall_score == 95
    assert result.stopping_reason == "threshold_met"
    assert [item.overall_score for item in result.evaluation_history] == [70, 95]
    assert result.improvement_metrics.score_delta == 25
    assert result.improvement_metrics.verified_delta == 2
    assert result.iteration_summaries[1].preserved == 2
    assert result.iteration_summaries[1].regenerated == 2
    final_ids = [case.id for case in result.test_generation.generated_test_cases]
    assert final_ids == ["TC-1", "TC-2", "TC-4"]
    feedback_payload = generator.generate.call_args.args[0]
    actions = feedback_payload["regeneration_plan"]["actions"]
    assert [item["test_case_id"] for item in actions] == ["TC-2", "TC-3"]
    assert feedback_payload["existing_test_case_count"] == 3
    assert feedback_payload["requested_regenerated_count"] == 2
    assert {
        item["id"] for item in feedback_payload["test_cases_to_improve"]
    } == {"TC-2", "TC-3"}
    assert {
        item["test_case_id"]
        for item in feedback_payload["regeneration_verification"]["results"]
    } == {"TC-1", "TC-2", "TC-3"}


def test_loop_stops_at_configured_iteration_limit() -> None:
    cases = [_case("TC-1", "Weak case")]
    generator, verifier, evaluator = Mock(), Mock(), Mock()
    generator.generate.return_value = _generation([_case("TC-2", "Still weak")])
    verifier.verify.side_effect = [
        _verification({"TC-1": "Partial"}),
        _verification({"TC-2": "Partial"}),
    ]
    evaluator.evaluate.side_effect = [_evaluation(50, 1), _evaluation(60, 2)]
    service = QualityLoopService(
        generator, verifier, evaluator, threshold=90, max_iterations=2
    )

    result = service.run({}, [], _generation(cases))

    assert result.iterations == 2
    assert result.quality_evaluation.threshold_met is False
    assert result.stopping_reason == "max_iterations"
    assert generator.generate.call_count == 1
    assert result.optimization_limit_reached is True
    assert result.iterations_performed == 2
    assert result.configured_iteration_limit == 2
    assert result.executed_regeneration_batches == 1
    assert result.configured_regeneration_batch_limit == 2
    assert result.final_quality_score == 60
    assert result.stop_reason == "max_iterations"


def test_loop_stops_after_one_regeneration_when_no_actionable_work_remains(
    caplog,
) -> None:
    cases = [_case("TC-1", "Weak case")]
    generator, verifier, evaluator = Mock(), Mock(), Mock()
    generator.generate.return_value = _generation([_case("TC-2", "Improved")])
    verifier.verify.side_effect = [
        _verification({"TC-1": "Partial"}),
        _verification({"TC-2": "Verified"}),
    ]
    evaluator.evaluate.side_effect = [_evaluation(70, 1), _evaluation(88, 2)]
    service = QualityLoopService(
        generator, verifier, evaluator, threshold=90, max_iterations=3
    )

    result = service.run({}, [], _generation(cases))

    assert result.iterations == 2
    assert result.stopping_reason == "max_iterations"
    assert generator.generate.call_count == 1
    assert "previous_score=70.0" in caplog.text
    assert "current_score=88.00" in caplog.text
    assert "regeneration_requested=False" in caplog.text


def test_loop_never_requests_same_missing_category_twice() -> None:
    cases = [_case("TC-1", "Weak case")]
    generator, verifier, evaluator = Mock(), Mock(), Mock()
    generator.generate.return_value = _generation([_case("TC-1", "Improved")])
    verifier.verify.side_effect = [
        _verification({"TC-1": "Partial"}),
        _verification({"TC-1": "Partial"}),
    ]
    evaluator.evaluate.side_effect = [
        _evaluation(70, 1, missing=["security"]),
        _evaluation(75, 2, missing=["security"]),
    ]
    service = QualityLoopService(
        generator, verifier, evaluator, threshold=90, max_iterations=3
    )

    result = service.run({}, [], _generation(cases))

    assert result.stopping_reason == "max_iterations"
    assert generator.generate.call_count == 1
    plan = generator.generate.call_args.args[0]["regeneration_plan"]
    assert plan["missing_categories"] == ["security"]


def test_loop_limits_regeneration_batches_and_preserves_generated_suite(
    caplog,
) -> None:
    cases = [_case("TC-1", "Weak case")]
    generator, verifier, evaluator = Mock(), Mock(), Mock()
    generator.generate.side_effect = [
        _generation([_case("TC-2", "First generated")]),
        _generation([_case("TC-3", "Second generated")]),
    ]
    verifier.verify.side_effect = [
        _verification({"TC-1": "Partial"}),
        _verification({"TC-2": "Verified", "TC-3": "Verified"}),
    ]
    actions = [
        RegenerationAction(
            action="ADD",
            category="positive",
            target_symbol=f"target_{index}",
            coverage_requirement=f"gap_{index}",
        )
        for index in range(5)
    ]
    first = _evaluation(60, 1).model_copy(update={
        "regeneration_plan": RegenerationPlan(
            current_score=60,
            threshold=90,
            actions=actions,
        )
    })
    evaluator.evaluate.side_effect = [first, _evaluation(95, 2)]
    service = QualityLoopService(
        generator,
        verifier,
        evaluator,
        threshold=90,
        regeneration_batch_size=1,
    )

    result = service.run({}, [], _generation(cases))

    assert generator.generate.call_count == 2
    assert {
        case.id for case in result.optimized_test_cases
    } == {"TC-2", "TC-3"}
    assert len(result.regeneration_plans[0].actions) == 5
    assert result.executed_regeneration_batches == 2
    assert result.configured_regeneration_batch_limit == 2
    assert result.optimization_limit_reached is True
    assert result.stop_reason == "threshold_met"
    assert "Quality regeneration batch limit reached" in caplog.text
    assert "===== QUALITY OPTIMIZATION SUMMARY =====" in caplog.text


def test_regeneration_batches_split_before_provider_selection_by_prompt_size() -> None:
    generator = Mock()
    generator.estimate_regeneration_prompt_tokens.side_effect = (
        lambda payload: (
            len(payload["regeneration_plan"]["actions"]) * 4_000
        )
    )
    service = QualityLoopService(
        generator, Mock(), Mock(),
        regeneration_batch_size=12,
        regeneration_prompt_token_limit=6_000,
    )
    actions = [
        RegenerationAction(
            action="ADD",
            category="positive",
            target_symbol=f"target_{index}",
        )
        for index in range(3)
    ]
    plan = RegenerationPlan(
        current_score=50, threshold=90, actions=actions
    )

    batches = service._prompt_sized_batches({}, plan, actions)

    assert [len(batch) for batch in batches] == [1, 1, 1]


def test_loop_uses_initial_verification_and_stops_when_no_replacements() -> None:
    cases = [_case("TC-1", "Weak case")]
    generator, verifier, evaluator = Mock(), Mock(), Mock()
    generator.generate.return_value = _generation([])
    evaluator.evaluate.return_value = _evaluation(50, 1)
    service = QualityLoopService(
        generator, verifier, evaluator, threshold=90, max_iterations=3
    )

    result = service.run(
        {},
        [],
        _generation(cases),
        initial_verification=_verification({"TC-1": "Partial"}),
    )

    assert result.stopping_reason == "no_improvements"
    assert result.optimized_test_cases == []
    verifier.verify.assert_not_called()


def test_loop_resumes_from_persisted_verification_without_repeating_it() -> None:
    cases = [_case("TC-1", "Verified case")]
    generation = _generation(cases)
    verification = _verification({"TC-1": "Verified"})
    generator, verifier, evaluator = Mock(), Mock(), Mock()
    evaluator.evaluate.return_value = _evaluation(95, 2)
    checkpoints = []
    service = QualityLoopService(generator, verifier, evaluator, threshold=90)

    result = service.run(
        {}, [], resume_state={
            "generation": generation,
            "verification": verification,
            "next_iteration": 2,
            "resume_point": "evaluation",
        }, checkpoint=lambda phase, payload: checkpoints.append((phase, payload)),
    )

    assert result.stopping_reason == "threshold_met"
    assert result.iterations == 2
    verifier.verify.assert_not_called()
    generator.generate.assert_not_called()
    assert checkpoints[0][0] == "verification"


def test_quality_loop_returns_partial_success_when_generation_providers_exhausted() -> None:
    cases = [_case("TC-1", "Weak case")]
    generator, verifier, evaluator = Mock(), Mock(), Mock()
    generator.generate.return_value = {
        **_generation([]),
        "generation_status": "partial_coverage_incomplete",
        "generation_reason": "all_providers_rate_limited",
        "uncovered_requirements": [{"symbol": "target"}],
    }
    evaluator.evaluate.return_value = _evaluation(50, 1)
    service = QualityLoopService(generator, verifier, evaluator, threshold=90)

    result = service.run(
        {}, [], _generation(cases),
        initial_verification=_verification({"TC-1": "Partial"}),
    )

    assert result.processing_status == "partial_success"
    assert result.stopping_reason == "provider_exhausted"
    assert result.final_exit_reason == "provider_exhausted"
    assert result.optimized_test_cases == []


def test_loop_rejects_weaker_individual_replacement() -> None:
    initial = [_case("TC-1", "Stronger existing")]
    replacement = [_case("TC-1", "Weaker regenerated")]
    generator, verifier, evaluator = Mock(), Mock(), Mock()
    generator.generate.return_value = _generation(replacement)
    existing_check = _verification({"TC-1": "Verified"})
    candidate_check = _verification({"TC-1": "Partial"})
    candidate_check["results"][0]["confidence"] = 0.7
    verifier.verify.side_effect = [existing_check, candidate_check]
    evaluator.evaluate.side_effect = [
        _evaluation(60, 1, improve=["TC-1"]),
        _evaluation(65, 2),
    ]
    service = QualityLoopService(generator, verifier, evaluator, threshold=90)

    result = service.run({}, [], _generation(initial))

    assert [case.title for case in result.optimized_test_suite] == [
        "Stronger existing"
    ]
    assert result.iteration_summaries[0].regenerated == 0
    generator.generate.assert_not_called()


def test_loop_excludes_unverified_tests_from_unexecuted_regeneration_batches() -> None:
    initial = [
        _case("TC-1", "First"),
        _case("TC-2", "Second"),
        _case("TC-3", "Third"),
    ]
    generator, verifier, evaluator = Mock(), Mock(), Mock()
    generator.generate.return_value = _generation([
        _case("TC-1", "Improved first")
    ])
    verifier.verify.side_effect = [
        _verification({
            "TC-1": "Partial", "TC-2": "Partial", "TC-3": "Partial"
        }),
        _verification({"TC-1": "Verified"}),
    ]
    actions = [
        RegenerationAction(action="UPDATE", test_case_id=f"TC-{index}")
        for index in range(1, 4)
    ]
    first = _evaluation(50, 1).model_copy(update={
        "regeneration_plan": RegenerationPlan(
            current_score=50, threshold=90, actions=actions,
        )
    })
    evaluator.evaluate.side_effect = [first, _evaluation(60, 2)]
    service = QualityLoopService(
        generator, verifier, evaluator, threshold=90,
        regeneration_batch_size=1,
        max_regeneration_batches_per_iteration=1,
    )

    result = service.run({}, [], _generation(initial))

    assert {case.id for case in result.optimized_test_suite} == {"TC-1"}
    assert next(
        case for case in result.optimized_test_suite if case.id == "TC-1"
    ).title == "Improved first"


def test_loop_returns_best_checkpoint_when_later_score_regresses() -> None:
    initial = [
        _case("TC-1", "Existing one"),
        _case("TC-2", "Existing two"),
    ]
    generator, verifier, evaluator = Mock(), Mock(), Mock()
    generator.generate.return_value = _generation([
        _case("TC-3", "Generated addition")
    ])
    verifier.verify.side_effect = [
        _verification({"TC-1": "Verified", "TC-2": "Verified"}),
        _verification({"TC-3": "Partial"}),
    ]
    evaluator.evaluate.side_effect = [
        _evaluation(80, 1, missing=["security"]),
        _evaluation(55, 2),
    ]
    checkpoints = []
    service = QualityLoopService(generator, verifier, evaluator, threshold=90)

    result = service.run(
        {}, [], _generation(initial),
        checkpoint=lambda phase, payload: checkpoints.append((phase, payload)),
    )

    assert result.iterations_performed == 2
    assert result.final_score == 80
    assert result.final_quality_score == 80
    assert result.improvement_metrics.score_delta == 0
    assert {case.id for case in result.optimized_test_suite} == {
        "TC-1", "TC-2"
    }
    assert result.quality_evaluation.iteration == 1
    assert any(
        payload.get("best_score") == 80
        and payload.get("best_suite")
        for _, payload in checkpoints
    )
