import uuid
from unittest.mock import Mock

import pytest
from sqlalchemy.exc import SQLAlchemyError

from app.database.models.code_understanding import CodeUnderstandingRun
from app.database.repositories.code_understanding_repository import (
    CodeUnderstandingRepository,
)
from app.schemas.test_case import TestCase as GeneratedTestCase
from app.schemas.test_quality import QualityLoopResult
from app.services.code_understanding.code_understanding_service import (
    CodeUnderstandingService,
)


def _optimization() -> dict:
    return {
        "test_generation": {"generated_test_cases": [{"id": "TC-2"}]},
        "test_verification": {"results": [{"test_case_id": "TC-2"}]},
        "quality_evaluation": {"overall_score": 95},
        "optimized_test_cases": [{"id": "TC-2"}],
        "evaluation_history": [{"overall_score": 70}, {"overall_score": 95}],
        "iteration_summaries": [{"iteration": 1}, {"iteration": 2}],
        "improvement_metrics": {"score_delta": 25},
        "stopping_reason": "threshold_met",
        "iterations": 2,
    }


def test_repository_persists_complete_optimization_without_losing_stage3() -> None:
    session = Mock()
    repository = CodeUnderstandingRepository(session)
    run = Mock(spec=CodeUnderstandingRun)
    run.id = uuid.uuid4()
    run.result = {"project_summary": "Preserve me", "architecture": "Layered"}
    optimization = _optimization()

    repository.save_quality_optimization(run, optimization)

    assert run.result["project_summary"] == "Preserve me"
    assert run.result["test_generation"] == optimization["test_generation"]
    assert run.result["test_verification"] == optimization["test_verification"]
    assert run.result["quality_evaluation"] == optimization["quality_evaluation"]
    persisted = run.result["quality_optimization"]
    assert persisted["optimized_test_cases"] == [{"id": "TC-2"}]
    assert len(persisted["evaluation_history"]) == 2
    assert len(persisted["iteration_summaries"]) == 2
    assert persisted["improvement_metrics"]["score_delta"] == 25
    session.commit.assert_called_once()
    session.refresh.assert_called_once_with(run)


def test_repository_persists_runtime_plan_without_losing_stage_artifacts() -> None:
    session = Mock()
    repository = CodeUnderstandingRepository(session)
    run = Mock(spec=CodeUnderstandingRun)
    run.id = uuid.uuid4()
    run.result = {
        "project_summary": "Preserve me",
        "quality_optimization": {"optimized_test_suite": []},
    }
    plan = {
        "targets": [],
        "issues": [],
        "total_tests": 0,
        "prepared_tests": 0,
        "unresolved_tests": 0,
    }

    repository.save_runtime_execution_plan(run, plan)

    assert run.result["project_summary"] == "Preserve me"
    assert run.result["quality_optimization"] == {
        "optimized_test_suite": []
    }
    assert run.result["runtime_execution_plan"] == plan
    session.commit.assert_called_once()
    session.refresh.assert_called_once_with(run)


def test_repository_logs_and_preserves_database_exception(caplog) -> None:
    session = Mock()
    failure = SQLAlchemyError("commit failed")
    session.commit.side_effect = failure
    repository = CodeUnderstandingRepository(session)
    run = Mock(spec=CodeUnderstandingRun)
    run.id = uuid.uuid4()
    run.result = {"project_summary": "Preserve me"}

    with pytest.raises(SQLAlchemyError) as raised:
        repository.save_quality_optimization(run, _optimization())

    assert raised.value is failure
    assert "method=save_quality_optimization" in caplog.text
    assert "entity=CodeUnderstandingRun" in caplog.text
    session.rollback.assert_called_once()


def test_repository_persists_generation_and_invalidates_downstream() -> None:
    session = Mock()
    repository = CodeUnderstandingRepository(session)
    run = Mock(spec=CodeUnderstandingRun)
    run.id = uuid.uuid4()
    run.result = {
        "project_summary": "Preserve me",
        "test_verification": {"stale": True},
        "quality_evaluation": {"stale": True},
        "quality_optimization": {"stale": True},
        "quality_checkpoint": {"stale": True},
        "runtime_execution_plan": {"stale": True},
    }
    generation = {"generated_test_cases": [], "total_generated": 0}

    repository.save_test_generation(run, generation)

    assert run.result["project_summary"] == "Preserve me"
    assert run.result["test_generation"] == generation
    version = run.result["artifact_versions"]["test_generation"][0]
    assert version["version"] == 1
    assert version["artifact"] == generation
    assert len(version["content_hash"]) == 64
    session.commit.assert_called_once_with()
    session.refresh.assert_called_once_with(run)


def test_repository_versions_regenerated_stage_artifacts_immutably() -> None:
    session = Mock()
    repository = CodeUnderstandingRepository(session)
    run = Mock(spec=CodeUnderstandingRun)
    run.id = uuid.uuid4()
    run.result = {"project_summary": "Preserve me"}

    repository.save_test_generation(run, {"generated_test_cases": [{"id": "UT-1"}]})
    first_snapshot = run.result["artifact_versions"]["test_generation"][0]
    repository.save_test_generation(run, {"generated_test_cases": [{"id": "UT-2"}]})

    history = run.result["artifact_versions"]["test_generation"]
    assert [item["version"] for item in history] == [1, 2]
    assert history[0] == first_snapshot
    assert history[0]["artifact"]["generated_test_cases"][0]["id"] == "UT-1"
    assert history[1]["artifact"]["generated_test_cases"][0]["id"] == "UT-2"
    assert session.commit.call_count == 2
    assert session.refresh.call_count == 2


def test_repository_atomically_prepares_completed_stage_four_rerun() -> None:
    session = Mock()
    repository = CodeUnderstandingRepository(session)
    run = Mock(spec=CodeUnderstandingRun)
    run.id = uuid.uuid4()
    run.result = {
        "project_summary": "Preserved Stage 3",
        "api_endpoints": [{"route": "/items"}],
        "test_generation": {"stale": True},
        "test_verification": {"stale": True},
        "quality_evaluation": {"stale": True},
        "quality_optimization": {"stale": True},
        "quality_checkpoint": {"stale": True},
        "runtime_execution_plan": {"stale": True},
    }

    repository.prepare_forced_rerun(run, start_stage="stage_4")

    assert run.result == {
        "project_summary": "Preserved Stage 3",
        "api_endpoints": [{"route": "/items"}],
    }
    assert run.status == "running"
    assert run.last_successful_stage == "stage_3"
    assert run.finished_at is None
    session.commit.assert_called_once_with()
    session.refresh.assert_called_once_with(run)


def test_repository_persists_verification_without_losing_prior_stages() -> None:
    session = Mock()
    repository = CodeUnderstandingRepository(session)
    run = Mock(spec=CodeUnderstandingRun)
    run.id = uuid.uuid4()
    generation = {"generated_test_cases": []}
    run.result = {
        "project_summary": "Preserve me",
        "test_generation": generation,
    }
    verification = {
        "results": [],
        "summary": {"verified": 0, "partial": 0, "failed": 0},
        "total_verified": 0,
    }

    repository.save_test_verification(run, verification)

    assert run.result["project_summary"] == "Preserve me"
    assert run.result["test_generation"] is generation
    assert run.result["test_verification"] is verification
    session.commit.assert_called_once_with()


def test_optimization_service_persists_loop_result() -> None:
    project_id, run_id = uuid.uuid4(), uuid.uuid4()
    run = Mock(spec=CodeUnderstandingRun)
    run.id = run_id
    optimized = Mock(spec=QualityLoopResult)
    optimized.model_dump.return_value = _optimization()
    loop = Mock()
    loop.run.return_value = optimized
    repository = Mock()
    service = object.__new__(CodeUnderstandingService)
    service._quality_loop_service = loop
    service._code_understanding_repository = repository
    service._load_stage3_artifact = Mock(return_value=({"project_summary": "x"}, run))
    service._load_source_files = Mock(return_value=[{"path": "app/main.py"}])
    test_case = GeneratedTestCase.model_validate(
        {
            "id": "TC-1",
            "title": "Test",
            "description": "Test",
            "category": "functional",
            "priority": "medium",
            "severity": "minor",
            "steps": ["Act"],
            "expected_results": ["Success"],
        }
    )

    result = service.optimize_test_quality(
        project_id,
        run_id,
        [test_case],
        {
            "results": [],
            "summary": {"verified": 0, "partial": 0, "failed": 0},
            "total_verified": 0,
        },
    )

    assert result is optimized
    repository.save_quality_optimization.assert_called_once_with(
        run, _optimization()
    )
    repository.save_runtime_execution_plan.assert_called_once()
