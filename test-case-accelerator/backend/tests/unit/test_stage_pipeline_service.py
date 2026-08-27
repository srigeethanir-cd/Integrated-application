import uuid
from unittest.mock import Mock

import pytest

from app.services.code_understanding.code_understanding_service import (
    CodeUnderstandingRunNotFoundError,
    CodeUnderstandingRunNotReadyError,
    CodeUnderstandingService,
)
from app.database.repositories.code_understanding_repository import (
    CodeUnderstandingRepository,
)


def _service_with_run(run):
    service = object.__new__(CodeUnderstandingService)
    service._code_understanding_repository = Mock()
    service._code_understanding_repository.get_by_id.return_value = run
    service._test_generation_agent = Mock()
    return service


def test_standalone_generation_reuses_only_stage_three_artifact() -> None:
    project_id = uuid.uuid4()
    run_id = uuid.uuid4()
    run = Mock(
        project_id=project_id,
        status="completed",
        result={
            "project_summary": "Example",
            "architecture": "Layered",
            "test_generation": {"old": "output"},
            "test_verification": {"old": "output"},
        },
    )
    service = _service_with_run(run)
    service._test_generation_agent.generate.return_value = {"generated_test_cases": []}

    result = service.generate_test_cases(project_id, run_id)

    assert result == {"generated_test_cases": []}
    service._test_generation_agent.generate.assert_called_once_with(
        {"project_summary": "Example", "architecture": "Layered"}
    )
    service._code_understanding_repository.save_test_generation.assert_called_once_with(
        run,
        {"generated_test_cases": []},
    )


def test_standalone_stage_rejects_unknown_run() -> None:
    service = _service_with_run(None)

    with pytest.raises(CodeUnderstandingRunNotFoundError):
        service.generate_test_cases(uuid.uuid4(), uuid.uuid4())


def test_standalone_stage_rejects_run_owned_by_another_project() -> None:
    run = Mock(project_id=uuid.uuid4(), status="completed", result={})
    service = _service_with_run(run)

    with pytest.raises(CodeUnderstandingRunNotReadyError):
        service.generate_test_cases(uuid.uuid4(), uuid.uuid4())


def test_understand_and_pipeline_select_expected_orchestration_mode() -> None:
    service = object.__new__(CodeUnderstandingService)
    service._execute_understanding = Mock(return_value="run")
    project_id = uuid.uuid4()
    dependency_run_id = uuid.uuid4()

    assert service.understand(project_id, dependency_run_id) == "run"
    service._execute_understanding.assert_called_with(
        project_id, dependency_run_id, include_pipeline=False
    )

    assert service.run(project_id, dependency_run_id) == "run"
    service._execute_understanding.assert_called_with(
        project_id, dependency_run_id, include_pipeline=True
    )


def test_execute_understanding_skips_completed_stages() -> None:
    project_id = uuid.uuid4()
    dependency_run_id = uuid.uuid4()
    
    project = Mock(id=project_id, storage_path="path")
    dependency_run = Mock(
        id=dependency_run_id,
        project_id=project_id,
        status="completed",
        files=[]
    )
    
    existing_run = Mock(
        id=uuid.uuid4(),
        status="failed",
        result={
            "project_summary": "Skipped stage 3 summary",
            "architecture": "Layered",
            "test_generation": {
                "generated_test_cases": [{"id": "STALE"}]
            },
            "test_verification": {"stale": True},
            "quality_optimization": {"stale": True},
            "runtime_execution_plan": {"stale": True},
        }
    )
    
    service = object.__new__(CodeUnderstandingService)
    service._project_repository = Mock()
    service._project_repository.get_by_id.return_value = project
    service._dependency_repository = Mock()
    service._dependency_repository.get_by_id.return_value = dependency_run
    service._code_understanding_repository = Mock()
    service._code_understanding_repository.get_by_dependency_run_id.return_value = [existing_run]
    
    service._resolve_source_directory = Mock(return_value=Mock())
    service._cache_manager = None
    
    service._agent = Mock()
    service._test_generation_agent = Mock()
    service._test_generation_agent.is_current_output.return_value = False
    service._test_generation_agent.generate.return_value = {"generated_test_cases": []}
    service._quality_loop_service = None
    service._test_verification_agent = None
    
    service._code_understanding_repository.complete.return_value = existing_run
    
    service._execute_understanding(
        project_id, dependency_run_id, include_pipeline=True
    )
    
    service._agent.analyze.assert_not_called()
    service._test_generation_agent.generate.assert_called_once()
    service._code_understanding_repository.save_test_generation.assert_called_once()
    completed_payload = service._code_understanding_repository.complete.call_args.args[1]
    assert completed_payload["test_generation"] == {"generated_test_cases": []}
    assert "test_verification" not in completed_payload
    assert "quality_optimization" not in completed_payload
    assert "runtime_execution_plan" not in completed_payload


def test_execute_understanding_rejects_concurrent_running_run() -> None:
    from app.services.code_understanding.code_understanding_service import CodeUnderstandingError
    project_id = uuid.uuid4()
    dependency_run_id = uuid.uuid4()
    
    project = Mock(id=project_id, storage_path="path")
    dependency_run = Mock(
        id=dependency_run_id,
        project_id=project_id,
        status="completed",
        files=[]
    )
    
    existing_run = Mock(
        id=uuid.uuid4(),
        status="running",
        result={
            "project_summary": "Active summary",
            "architecture": "Layered"
        }
    )
    
    service = object.__new__(CodeUnderstandingService)
    service._project_repository = Mock()
    service._project_repository.get_by_id.return_value = project
    service._dependency_repository = Mock()
    service._dependency_repository.get_by_id.return_value = dependency_run
    service._code_understanding_repository = Mock()
    service._code_understanding_repository.get_by_dependency_run_id.return_value = [existing_run]
    
    with pytest.raises(CodeUnderstandingError, match="resume is already running"):
        service._execute_understanding(project_id, dependency_run_id, include_pipeline=True)


def test_retry_resumes_same_failed_run_and_increments_attempt() -> None:
    run = Mock(
        id=uuid.uuid4(),
        project_id=uuid.uuid4(),
        dependency_run_id=uuid.uuid4(),
        status="failed",
        failed_stage="stage_3",
    )
    service = _service_with_run(run)
    service._execute_understanding = Mock(return_value=run)

    assert service.retry(run.id) is run

    service._code_understanding_repository.prepare_retry.assert_called_once_with(run)
    service._execute_understanding.assert_called_once_with(
        run.project_id,
        run.dependency_run_id,
        include_pipeline=True,
        resume_run_id=run.id,
    )


def test_retry_rejects_completed_run() -> None:
    run = Mock(status="completed")
    service = _service_with_run(run)

    with pytest.raises(CodeUnderstandingRunNotReadyError):
        service.retry(uuid.uuid4())


def test_retry_preserves_completed_stages_and_resets_only_downstream() -> None:
    run = Mock(
        failed_stage="stage_5",
        result={
            "project_summary": "keep",
            "test_generation": {"generated_test_cases": [{"id": "TC-1"}]},
            "test_verification": {"partial": True},
            "quality_optimization": {"stale": True},
            "runtime_execution_plan": {"stale": True},
        },
        retry_count=1,
    )
    repository = CodeUnderstandingRepository(Mock())

    repository.prepare_retry(run)

    assert run.retry_count == 2
    assert run.result == {
        "project_summary": "keep",
        "test_generation": {"generated_test_cases": [{"id": "TC-1"}]},
    }


def test_force_rerun_stage_four_uses_same_completed_run() -> None:
    project_id, dependency_run_id = uuid.uuid4(), uuid.uuid4()
    run = Mock(
        id=uuid.uuid4(),
        project_id=project_id,
        dependency_run_id=dependency_run_id,
        status="completed",
    )
    service = object.__new__(CodeUnderstandingService)
    service._code_understanding_repository = Mock()
    service._code_understanding_repository.get_by_dependency_run_id.return_value = [
        run
    ]
    service._execute_understanding = Mock(return_value=run)

    result = service.force_rerun(
        project_id, dependency_run_id, start_stage="test_generation"
    )

    assert result is run
    service._code_understanding_repository.prepare_forced_rerun.assert_called_once_with(
        run, start_stage="stage_4"
    )
    service._execute_understanding.assert_called_once_with(
        project_id,
        dependency_run_id,
        include_pipeline=True,
        resume_run_id=run.id,
    )
