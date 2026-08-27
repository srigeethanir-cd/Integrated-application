from unittest.mock import Mock

from app.dependencies.project import (
    get_github_clone_service,
    get_project_repository,
    get_upload_service,
)
from app.dependencies.workflow import get_workflow_service
from app.main import app
from app.services.workflow_service import WorkflowResult
from app.database.models.code_understanding import CodeUnderstandingStatus


def test_github_workflow_runs_automatically_through_stage_four(client, project_factory) -> None:
    project = project_factory()
    clone_service = Mock()
    clone_service.clone_project.return_value = project
    workflow_service = Mock()
    workflow_service.run_through_stage_four.return_value = WorkflowResult(
        project=project,
        current_stage="stage_4",
        status="waiting_for_approval",
        completed_stage="stage_4",
        next_stage=None,
    )
    app.dependency_overrides[get_github_clone_service] = lambda: clone_service
    app.dependency_overrides[get_workflow_service] = lambda: workflow_service

    response = client.post(
        "/workflows/github",
        json={
            "github_url": "https://github.com/openai/example",
            "name": "Example",
            "description": "Project",
        },
    )

    assert response.status_code == 201
    assert response.json()["current_stage"] == "stage_4"
    assert response.json()["status"] == "waiting_for_approval"
    assert response.json()["next_stage"] is None
    workflow_service.run_through_stage_four.assert_called_once_with(project)
    workflow_service.run.assert_not_called()


def test_upload_workflow_runs_automatically_through_stage_four(client, project_factory) -> None:
    project = project_factory()
    upload_service = Mock()
    upload_service.upload_project.return_value = project
    workflow_service = Mock()
    workflow_service.run_through_stage_four.return_value = WorkflowResult(
        project=project,
        current_stage="stage_4",
        status="waiting_for_approval",
        completed_stage="stage_4",
        next_stage=None,
    )
    app.dependency_overrides[get_upload_service] = lambda: upload_service
    app.dependency_overrides[get_workflow_service] = lambda: workflow_service

    response = client.post(
        "/workflows/upload",
        data={"name": "Example", "description": "Project"},
        files={"uploaded_file": ("project.zip", b"zip-content", "application/zip")},
    )

    assert response.status_code == 201
    assert response.json()["completed_stage"] == "stage_4"
    assert response.json()["dependency"] is None
    assert response.json()["security_scan"] is None
    assert response.json()["pipeline"] is None
    workflow_service.run_through_stage_four.assert_called_once_with(project)
    workflow_service.run.assert_not_called()


def test_continue_endpoint_executes_one_transition(client, project_factory) -> None:
    project = project_factory()
    project_repository = Mock()
    project_repository.get_by_id.return_value = project
    workflow_service = Mock()
    workflow_service.continue_from.return_value = WorkflowResult(
        project=project,
        current_stage="stage_2",
        completed_stage="stage_2",
        next_stage="stage_3",
    )
    app.dependency_overrides[get_project_repository] = lambda: project_repository
    app.dependency_overrides[get_workflow_service] = lambda: workflow_service

    response = client.post(
        f"/workflows/{project.id}/continue",
        json={"from_stage": "stage_1"},
    )

    assert response.status_code == 200
    assert response.json()["completed_stage"] == "stage_2"
    assert response.json()["next_stage"] == "stage_3"
    workflow_service.continue_from.assert_called_once_with(project, "stage_1")


def test_continue_endpoint_approves_stage_three_and_returns_stage_four(
    client, project_factory,
) -> None:
    project = project_factory()
    project_repository = Mock()
    project_repository.get_by_id.return_value = project
    generation = {
        "generated_test_cases": [],
        "coverage_summary": {},
        "total_generated": 0,
        "total_after_deduplication": 0,
    }
    workflow_service = Mock()
    workflow_service.continue_from.return_value = WorkflowResult(
        project=project,
        current_stage="stage_4",
        status="waiting_for_approval",
        completed_stage="stage_4",
        next_stage=None,
        test_generation=generation,
    )
    app.dependency_overrides[get_project_repository] = lambda: project_repository
    app.dependency_overrides[get_workflow_service] = lambda: workflow_service

    response = client.post(
        f"/workflows/{project.id}/continue",
        json={"from_stage": "stage_3"},
    )

    assert response.status_code == 200
    assert response.json()["completed_stage"] == "stage_4"
    assert response.json()["generation"] == {
        **generation,
        "generation_status": "complete",
        "uncovered_requirements": [],
    }
    workflow_service.continue_from.assert_called_once_with(project, "stage_3")


def test_openapi_exposes_workflow_and_independent_stage_routes(client) -> None:
    paths = client.get("/openapi.json").json()["paths"]

    assert "/workflows/upload" in paths
    assert "/workflows/github" in paths
    assert "/workflows/{project_id}/continue" in paths
    assert "/workflows/{project_id}/state" in paths
    assert "/projects/upload" in paths
    assert "/projects/{project_id}/dependencies" in paths
    assert "/projects/{project_id}/understand" in paths


def test_workflow_state_strips_internal_artifact_metadata(
    client, project_factory,
) -> None:
    project = project_factory()
    project_repository = Mock()
    project_repository.get_by_id.return_value = project
    persisted_result = {
        "project_summary": "Partial Stage 3 result",
        "architecture": "Layered",
        "_artifact_version": {"composite": "internal"},
        "artifact_versions": {"test_generation": []},
        "quality_checkpoint": {"processing_status": "in_progress"},
    }
    run = Mock(
        id=project.id,
        status=CodeUnderstandingStatus.COMPLETED,
        result=persisted_result,
        failed_stage=None,
        failure_reason=None,
        retry_count=0,
        last_successful_stage="stage_3",
    )
    workflow_service = Mock()
    workflow_service.state.return_value = WorkflowResult(
        project=project,
        current_stage="stage_3",
        completed_stage="stage_3",
        next_stage="stage_4",
        code_understanding_run=run,
    )
    app.dependency_overrides[get_project_repository] = lambda: project_repository
    app.dependency_overrides[get_workflow_service] = lambda: workflow_service

    response = client.get(f"/workflows/{project.id}/state")

    assert response.status_code == 200
    result = response.json()["pipeline"]["result"]
    assert result["project_summary"] == "Partial Stage 3 result"
    assert "_artifact_version" not in result
    assert result["artifact_versions"] == {"test_generation": []}
    assert "quality_checkpoint" not in result
    assert persisted_result["_artifact_version"] == {"composite": "internal"}
