import uuid
from unittest.mock import Mock

from app.dependencies.dependency import get_dependency_service
from app.main import app
from app.services.dependency.dependency_service import (
    NoSupportedSourceFilesError,
)


def test_dependency_discovery_uses_project_scoped_endpoint(client) -> None:
    project_id = uuid.uuid4()
    run_id = uuid.uuid4()
    service = Mock()
    service.run.return_value = Mock(id=run_id, status="completed")
    app.dependency_overrides[get_dependency_service] = lambda: service

    response = client.post(f"/projects/{project_id}/dependencies")

    assert response.status_code == 201
    assert response.json() == {"run_id": str(run_id), "status": "completed"}
    service.run.assert_called_once_with(project_id)


def test_dependency_discovery_returns_not_found_for_unknown_project(client) -> None:
    project_id = uuid.uuid4()
    service = Mock()
    service.run.return_value = None
    app.dependency_overrides[get_dependency_service] = lambda: service

    response = client.post(f"/projects/{project_id}/dependencies")

    assert response.status_code == 404


def test_dependency_discovery_reports_no_supported_source_files(client) -> None:
    project_id = uuid.uuid4()
    service = Mock()
    service.run.side_effect = NoSupportedSourceFilesError(
        "No supported source files were found in the repository."
    )
    app.dependency_overrides[get_dependency_service] = lambda: service

    response = client.post(f"/projects/{project_id}/dependencies")

    assert response.status_code == 422
    assert response.json() == {
        "detail": "No supported source files were found in the repository."
    }


def test_get_latest_dependency_run(client) -> None:
    project_id, run_id = uuid.uuid4(), uuid.uuid4()
    service = Mock()
    service.get_latest_run.return_value = Mock(
        id=run_id,
        project_id=project_id,
        project_path="/storage/project/source",
        status="completed",
        files=[],
    )
    app.dependency_overrides[get_dependency_service] = lambda: service

    response = client.get(f"/projects/{project_id}/dependency-runs/latest")

    assert response.status_code == 200
    assert response.json()["run_id"] == str(run_id)
    service.get_latest_run.assert_called_once_with(project_id)
