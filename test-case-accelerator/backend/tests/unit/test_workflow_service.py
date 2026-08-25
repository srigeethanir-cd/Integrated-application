import uuid
import threading
from concurrent.futures import Future
from unittest.mock import Mock, call

import pytest

from app.services.workflow_service import WorkflowError, WorkflowService


def test_workflow_runs_stages_in_order() -> None:
    project = Mock(id=uuid.uuid4())
    dependency_run = Mock(id=uuid.uuid4())
    pipeline_run = Mock(id=uuid.uuid4())
    dependency_service = Mock()
    dependency_service.run.return_value = dependency_run
    pipeline_service = Mock()
    pipeline_service.run.return_value = pipeline_run
    security_run = Mock(status="completed")
    security_service = Mock()
    security_service.run.return_value = security_run
    workflow = WorkflowService(dependency_service, security_service, pipeline_service)

    result = workflow.run(project)

    dependency_service.run.assert_called_once_with(project.id)
    pipeline_service.run.assert_called_once_with(project.id, dependency_run.id)
    assert result.project is project
    assert result.security_scan_run is security_run
    assert result.dependency_run is dependency_run
    assert result.code_understanding_run is pipeline_run


def test_workflow_runs_security_in_parallel_and_joins_before_understanding() -> None:
    project = Mock(id=uuid.uuid4())
    dependency_run = Mock(id=uuid.uuid4())
    security_run = Mock(status="completed")
    security_started = threading.Event()
    allow_security_to_finish = threading.Event()
    security_thread: Future[int] = Future()
    request_thread = threading.get_ident()

    def run_security(*_args, **_kwargs):
        security_thread.set_result(threading.get_ident())
        security_started.set()
        assert allow_security_to_finish.wait(timeout=2)
        return security_run

    def run_dependency(_project_id):
        assert threading.get_ident() == request_thread
        assert security_started.wait(timeout=2)
        allow_security_to_finish.set()
        return dependency_run

    security_service = Mock()
    security_service.run.side_effect = run_security
    dependency_service = Mock()
    dependency_service.run.side_effect = run_dependency
    pipeline_service = Mock()
    workflow = WorkflowService(
        dependency_service, security_service, pipeline_service
    )

    workflow.run(project)

    assert security_thread.result() != request_thread
    pipeline_service.run.assert_called_once_with(project.id, dependency_run.id)


def test_workflow_stops_when_stage_two_cannot_find_project() -> None:
    project = Mock(id=uuid.uuid4())
    dependency_service = Mock()
    dependency_service.run.return_value = None
    pipeline_service = Mock()
    security_service = Mock()
    security_service.run.return_value = Mock(status="completed")

    with pytest.raises(WorkflowError):
        WorkflowService(dependency_service, security_service, pipeline_service).run(project)

    pipeline_service.run.assert_not_called()


def test_workflow_resume_skips_completed_dependency_run() -> None:
    project = Mock(id=uuid.uuid4())
    dependency_run = Mock(id=uuid.uuid4(), status="completed")
    pipeline_run = Mock(id=uuid.uuid4())
    dependency_service = Mock()
    pipeline_service = Mock()
    pipeline_service.get_latest_pipeline_state.return_value = {
        "dependency_run": dependency_run,
        "understanding_run": None,
    }
    pipeline_service.run.return_value = pipeline_run
    security_run = Mock(status="completed")
    security_service = Mock()
    security_service.get_latest_run.return_value = security_run
    
    workflow = WorkflowService(dependency_service, security_service, pipeline_service)
    result = workflow.resume(project)
    
    dependency_service.run.assert_not_called()
    pipeline_service.get_latest_pipeline_state.assert_called_once_with(project.id)
    pipeline_service.run.assert_called_once_with(project.id, dependency_run.id)
    assert result.dependency_run is dependency_run


def test_workflow_resume_runs_stage_two_if_not_completed() -> None:
    project = Mock(id=uuid.uuid4())
    dependency_run = Mock(id=uuid.uuid4(), status="failed")
    new_dependency_run = Mock(id=uuid.uuid4(), status="completed")
    pipeline_run = Mock(id=uuid.uuid4())
    dependency_service = Mock()
    dependency_service.run.return_value = new_dependency_run
    pipeline_service = Mock()
    pipeline_service.get_latest_pipeline_state.return_value = {
        "dependency_run": dependency_run,
        "understanding_run": None,
    }
    pipeline_service.run.return_value = pipeline_run
    security_run = Mock(status="completed")
    security_service = Mock()
    security_service.get_latest_run.return_value = security_run
    
    workflow = WorkflowService(dependency_service, security_service, pipeline_service)
    result = workflow.resume(project)
    
    dependency_service.run.assert_called_once_with(project.id)
    pipeline_service.run.assert_called_once_with(project.id, new_dependency_run.id)
    assert result.dependency_run is new_dependency_run


def test_workflow_force_reruns_completed_pipeline_from_stage_four() -> None:
    project = Mock(id=uuid.uuid4())
    dependency_run = Mock(id=uuid.uuid4(), status="completed")
    pipeline_run = Mock(id=uuid.uuid4(), status="completed")
    dependency_service = Mock()
    pipeline_service = Mock()
    pipeline_service.get_latest_pipeline_state.return_value = {
        "dependency_run": dependency_run,
        "understanding_run": pipeline_run,
    }
    pipeline_service.force_rerun.return_value = pipeline_run
    security_run = Mock(status="completed")
    security_service = Mock()
    security_service.get_latest_run.return_value = security_run
    workflow = WorkflowService(
        dependency_service, security_service, pipeline_service
    )

    result = workflow.resume(
        project, start_stage="test_generation", force=True
    )

    dependency_service.run.assert_not_called()
    security_service.run.assert_not_called()
    pipeline_service.run.assert_not_called()
    pipeline_service.force_rerun.assert_called_once_with(
        project.id,
        dependency_run.id,
        start_stage="test_generation",
    )
    assert result.code_understanding_run is pipeline_run


def test_continue_from_stage_one_runs_only_stage_two() -> None:
    project = Mock(id=uuid.uuid4())
    dependency_run = Mock(id=uuid.uuid4(), status="completed")
    security_run = Mock(status="completed")
    dependency_service = Mock()
    dependency_service.get_latest_workflow_run.return_value = None
    dependency_service.run.return_value = dependency_run
    security_service = Mock()
    security_service.get_latest_run.return_value = None
    security_service.run.return_value = security_run
    understanding_service = Mock()
    understanding_service.get_latest_workflow_run.return_value = None
    workflow = WorkflowService(
        dependency_service, security_service, understanding_service
    )

    result = workflow.continue_from(project, "stage_1")

    assert result.completed_stage == "stage_2"
    assert result.next_stage == "stage_3"
    dependency_service.run.assert_called_once_with(project.id)
    security_service.run.assert_called_once_with(
        project.id, resume_failed=True
    )
    understanding_service.understand.assert_not_called()


def test_continue_from_stage_two_runs_only_stage_three() -> None:
    project = Mock(id=uuid.uuid4())
    dependency_run = Mock(id=uuid.uuid4(), status="completed")
    security_run = Mock(status="completed")
    understanding_run = Mock(status="completed")
    dependency_service = Mock()
    dependency_service.get_latest_workflow_run.return_value = dependency_run
    security_service = Mock()
    security_service.get_latest_run.return_value = security_run
    understanding_service = Mock()
    understanding_service.get_latest_workflow_run.return_value = None
    understanding_service.understand.return_value = understanding_run
    workflow = WorkflowService(
        dependency_service, security_service, understanding_service
    )

    result = workflow.continue_from(project, "stage_2")

    assert result.completed_stage == "stage_3"
    assert result.next_stage == "stage_4"
    understanding_service.understand.assert_called_once_with(
        project.id, dependency_run.id
    )
    dependency_service.run.assert_not_called()
    security_service.run.assert_not_called()


def test_continue_from_stage_three_approves_and_runs_only_stage_four() -> None:
    project = Mock(id=uuid.uuid4())
    dependency_run = Mock(id=uuid.uuid4(), status="completed")
    security_run = Mock(status="completed")
    understanding_run = Mock(id=uuid.uuid4(), status="completed", result={})
    dependency_service = Mock()
    dependency_service.get_latest_workflow_run.return_value = dependency_run
    security_service = Mock()
    security_service.get_latest_run.return_value = security_run
    understanding_service = Mock()
    understanding_service.get_latest_workflow_run.return_value = understanding_run
    generation = {
        "generated_test_cases": [],
        "coverage_summary": {},
        "total_generated": 0,
        "total_after_deduplication": 0,
    }
    understanding_service.generate_test_cases.return_value = generation
    workflow = WorkflowService(
        dependency_service, security_service, understanding_service
    )

    result = workflow.continue_from(project, "stage_3")

    assert result.current_stage == "stage_4"
    assert result.status == "waiting_for_approval"
    assert result.test_generation is generation
    understanding_service.generate_test_cases.assert_called_once_with(
        project.id, understanding_run.id
    )
    understanding_service.understand.assert_not_called()


def test_automatic_preprocessing_runs_sequentially_through_stage_four() -> None:
    project = Mock(id=uuid.uuid4())
    workflow = Mock(spec=WorkflowService)
    stage_two = Mock(current_stage="stage_2", status="waiting_for_approval")
    stage_three = Mock(current_stage="stage_3", status="waiting_for_approval")
    stage_four = Mock(current_stage="stage_4", status="waiting_for_approval")
    workflow.continue_from.side_effect = [stage_two, stage_three, stage_four]

    result = WorkflowService.run_through_stage_four(workflow, project)

    assert result is stage_four
    assert workflow.continue_from.call_args_list == [
        call(project, "stage_1"),
        call(project, "stage_2"),
        call(project, "stage_3"),
    ]


def test_automatic_preprocessing_stops_at_failed_stage() -> None:
    project = Mock(id=uuid.uuid4())
    workflow = Mock(spec=WorkflowService)
    failed = Mock(current_stage="stage_2", status="failed")
    workflow.continue_from.return_value = failed

    result = WorkflowService.run_through_stage_four(workflow, project)

    assert result is failed
    workflow.continue_from.assert_called_once_with(project, "stage_1")


def test_retry_from_failed_stage_four_reruns_only_test_generation() -> None:
    project = Mock(id=uuid.uuid4())
    dependency_run = Mock(id=uuid.uuid4(), status="completed")
    security_run = Mock(status="completed")
    understanding_run = Mock(
        id=uuid.uuid4(),
        status="failed",
        failed_stage="stage_4",
        failure_reason="generation failed",
        result={"project_summary": "preserved Stage 3"},
    )
    dependency_service = Mock()
    dependency_service.get_latest_workflow_run.return_value = dependency_run
    security_service = Mock()
    security_service.get_latest_run.return_value = security_run
    understanding_service = Mock()
    understanding_service.get_latest_workflow_run.return_value = understanding_run
    generation = {
        "generated_test_cases": [],
        "coverage_summary": {},
        "total_generated": 0,
        "total_after_deduplication": 0,
    }
    understanding_service.retry_test_generation.return_value = generation
    workflow = WorkflowService(
        dependency_service, security_service, understanding_service
    )

    result = workflow.continue_from(project, "stage_3")

    assert result.current_stage == "stage_4"
    assert result.status == "waiting_for_approval"
    understanding_service.retry_test_generation.assert_called_once_with(
        project.id, understanding_run.id
    )
    understanding_service.generate_test_cases.assert_not_called()
    understanding_service.understand.assert_not_called()


def test_retry_reruns_only_failed_stage_two_branch() -> None:
    project = Mock(id=uuid.uuid4())
    completed_dependency = Mock(id=uuid.uuid4(), status="completed")
    failed_scan = Mock(status="failed", error_message="scan failed")
    completed_scan = Mock(status="completed")
    dependency_service = Mock()
    dependency_service.get_latest_workflow_run.return_value = completed_dependency
    security_service = Mock()
    security_service.get_latest_run.return_value = failed_scan
    security_service.run.return_value = completed_scan
    understanding_service = Mock()
    understanding_service.get_latest_workflow_run.return_value = None
    workflow = WorkflowService(
        dependency_service, security_service, understanding_service
    )

    result = workflow.continue_from(project, "stage_1")

    assert result.completed_stage == "stage_2"
    dependency_service.run.assert_not_called()
    security_service.run.assert_called_once_with(
        project.id, resume_failed=True
    )
