import uuid
from datetime import UTC, datetime
from unittest.mock import Mock

from app.dependencies.project import get_project_repository
from app.dependencies.workflow import get_workflow_service
from app.main import app
from app.services.workflow_service import WorkflowResult


def test_completed_workflow_can_force_rerun_from_test_generation(
    client, project_factory,
) -> None:
    project = project_factory()
    now = datetime.now(UTC)
    dependency_run = Mock(
        id=uuid.uuid4(),
        project_id=project.id,
        project_path="projects/example/source",
        status="completed",
        files=[],
    )
    security_run = Mock(
        id=uuid.uuid4(),
        project_id=project.id,
        status="completed",
        summary=None,
        error_message=None,
        retry_count=0,
        created_at=now,
        started_at=now,
        finished_at=now,
        findings=[],
    )
    pipeline_run = Mock(
        id=uuid.uuid4(),
        status="completed",
        result=None,
        failed_stage=None,
        failure_reason=None,
        retry_count=0,
        last_successful_stage="stage_3",
    )
    project_repository = Mock()
    project_repository.get_by_id.return_value = project
    workflow_service = Mock()
    workflow_service.resume.return_value = WorkflowResult(
        project=project,
        security_scan_run=security_run,
        dependency_run=dependency_run,
        code_understanding_run=pipeline_run,
    )
    app.dependency_overrides[get_project_repository] = (
        lambda: project_repository
    )
    app.dependency_overrides[get_workflow_service] = lambda: workflow_service

    response = client.post(
        f"/workflows/{project.id}/resume",
        json={"start_stage": "test_generation", "force": True},
    )

    assert response.status_code == 200, response.json()
    assert response.json()["pipeline"]["run_id"] == str(pipeline_run.id)
    workflow_service.resume.assert_called_once_with(
        project,
        start_stage="test_generation",
        force=True,
    )


def test_resume_without_body_preserves_existing_call_contract(
    client, project_factory,
) -> None:
    project = project_factory()
    project_repository = Mock()
    project_repository.get_by_id.return_value = project
    workflow_service = Mock()
    workflow_service.resume.side_effect = RuntimeError("contract checked")
    app.dependency_overrides[get_project_repository] = (
        lambda: project_repository
    )
    app.dependency_overrides[get_workflow_service] = lambda: workflow_service

    try:
        client.post(f"/workflows/{project.id}/resume")
    except RuntimeError:
        pass

    workflow_service.resume.assert_called_once_with(project)
