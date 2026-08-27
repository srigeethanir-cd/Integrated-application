import json

from app.agents.quality_evaluation.agent import TestQualityEvaluationAgent as Evaluator


def test_deterministic_evaluation_scores_all_dimensions_and_feedback() -> None:
    cases = [
        {
            "id": "TC-1",
            "title": "Create project",
            "description": "Create project",
            "category": "functional",
            "priority": "high",
            "severity": "major",
            "steps": ["Submit project"],
            "expected_results": ["Project is created"],
            "traceability": {"symbol": "create_project"},
        }
    ]
    verification = {
        "results": [
            {
                "test_case_id": "TC-1",
                "status": "Partial",
                "confidence": 0.5,
                "evidence": [],
                "findings": [],
            }
        ],
        "summary": {"verified": 0, "partial": 1, "failed": 0},
        "total_verified": 0,
    }

    result = Evaluator().evaluate(
        cases,
        verification,
        {"test_targets": [{"symbol": "create_project"}]},
        threshold=90,
        iteration=1,
    )

    assert 0 <= result.overall_score < 90
    assert result.dimension_scores.coverage == 100
    assert result.dimension_scores.correctness == 50
    assert result.dimension_scores.boundary_coverage == 0
    assert result.dimension_scores.negative_testing == 0
    assert result.dimension_scores.security == 0
    assert result.dimension_scores.performance == 0
    assert result.dimension_scores.duplicate_quality == 100
    assert result.feedback.improve_test_case_ids == ["TC-1"]
    assert result.threshold_met is False
    assert result.regeneration_plan is not None
    assert result.regeneration_plan.current_score == result.overall_score
    assert result.regeneration_plan.threshold == 90
    assert any(
        action.action == "UPDATE"
        and action.test_case_id == "TC-1"
        for action in result.regeneration_plan.actions
    )


def test_ai_evaluation_is_normalized_to_configured_threshold_and_iteration() -> None:
    baseline = Evaluator().evaluate(
        [],
        {
            "results": [],
            "summary": {"verified": 0, "partial": 0, "failed": 0},
            "total_verified": 0,
        },
        {},
        threshold=90,
        iteration=1,
    )
    provider = type(
        "Provider",
        (),
        {
            "generate_structured": lambda self, **kwargs: baseline.model_copy(
                update={"overall_score": 92, "threshold_met": False, "iteration": 99}
            )
        },
    )()

    result = Evaluator(client=provider).evaluate(
        [],
        {
            "results": [],
            "summary": {"verified": 0, "partial": 0, "failed": 0},
            "total_verified": 0,
        },
        {},
        threshold=90,
        iteration=2,
    )

    assert result.overall_score == 0
    assert result.threshold_met is False
    assert result.iteration == 2


def test_stage6_ai_prompt_is_compact_and_capacity_aware() -> None:
    class Provider:
        request = None

        def generate_structured_capacity_aware(self, **kwargs):
            self.request = kwargs
            raise RuntimeError("temporarily unavailable")

        def generate_structured(self, **kwargs):
            raise AssertionError("Stage 6 must use capacity-aware routing")

    provider = Provider()
    case = {
        "id": "TC-1",
        "title": "Create project",
        "description": "FULL_CASE_DESCRIPTION_SENTINEL",
        "category": "positive",
        "priority": "high",
        "severity": "major",
        "steps": ["FULL_CASE_STEPS_SENTINEL"],
        "expected_results": ["Created"],
        "traceability": {"symbol": "create_project"},
    }
    verification = {
        "results": [{
            "test_case_id": "TC-1",
            "status": "Failed",
            "confidence": 0.5,
            "evidence": [{
                "file": "projects.py",
                "detail": "RAW_EVIDENCE_SENTINEL",
            }],
            "findings": [{
                "check": "behavior_semantics",
                "status": "Failed",
                "detail": "Expected creation",
                "evidence": [],
            }],
        }],
        "summary": {"verified": 0, "partial": 0, "failed": 1},
        "total_verified": 0,
    }

    Evaluator(client=provider).evaluate(
        [case],
        verification,
        {
            "test_targets": [{"symbol": "create_project"}],
            "project_summary": "FULL_STAGE3_SENTINEL",
        },
        threshold=90,
        iteration=1,
    )

    payload = json.loads(provider.request["user_prompt"])
    serialized = provider.request["user_prompt"]
    assert payload["suite_summary"]["total_tests"] == 1
    assert payload["weak_test_cases"][0]["id"] == "TC-1"
    assert "FULL_CASE_DESCRIPTION_SENTINEL" not in serialized
    assert "FULL_CASE_STEPS_SENTINEL" not in serialized
    assert "RAW_EVIDENCE_SENTINEL" not in serialized
    assert "FULL_STAGE3_SENTINEL" not in serialized


def test_quality_is_gated_by_discovered_target_coverage_and_failed_evidence() -> None:
    cases = [{
        "id": "TC-1", "title": "Valid login", "description": "Login succeeds",
        "category": "positive", "priority": "high", "severity": "major",
        "steps": ["Log in"], "expected_results": ["Access granted"],
        "traceability": {"symbol": "login", "symbols": ["login"]},
    }]
    verification = {
        "results": [{"test_case_id": "TC-1", "status": "Failed", "confidence": .95,
                     "evidence": [], "findings": []}],
        "summary": {"verified": 0, "partial": 0, "failed": 1}, "total_verified": 0,
    }
    stage3 = {"test_targets": [
        {"symbol": "login", "file": "auth.py", "behavior": "Login"},
        {"symbol": "transfer", "file": "transaction.py", "behavior": "Transfer"},
    ]}

    result = Evaluator().evaluate(cases, verification, stage3, threshold=90, iteration=1)

    assert result.dimension_scores.coverage == 50
    assert result.dimension_scores.completeness == 50
    assert result.dimension_scores.correctness == 0
    assert result.overall_score <= 50
    assert result.threshold_met is False
    assert "performance" not in " ".join(result.recommendations).lower()
