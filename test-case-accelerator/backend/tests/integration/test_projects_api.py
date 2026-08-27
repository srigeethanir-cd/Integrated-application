import uuid
from collections.abc import Callable
from unittest.mock import MagicMock

from fastapi.testclient import TestClient

from app.database.models.project import Project, ProjectSourceType
from app.database.repositories.project_repository import ProjectRepository
from app.dependencies.project import (
    get_github_clone_service,
    get_project_deletion_service,
    get_project_repository,
    get_upload_service,
)
from app.main import app
from app.services.ingestion.github_clone_service import GitHubCloneService
from app.services.ingestion.project_deletion_service import ProjectDeletionService
from app.services.ingestion.upload_service import UploadService


def test_upload_project_endpoint(
    client: TestClient,
    project_factory: Callable[..., Project],
) -> None:
    project = project_factory()
    service = MagicMock(spec=UploadService)
    service.upload_project.return_value = project
    app.dependency_overrides[get_upload_service] = lambda: service

    response = client.post(
        "/projects/upload",
        data={"name": "Example project", "description": "Description"},
        files={"uploaded_file": ("project.zip", b"archive", "application/zip")},
    )

    assert response.status_code == 201
    assert response.json()["id"] == str(project.id)
    service.upload_project.assert_called_once()


def test_clone_github_project_endpoint(
    client: TestClient,
    project_factory: Callable[..., Project],
) -> None:
    project = project_factory(
        source_type=ProjectSourceType.GITHUB,
        github_url="https://github.com/openai/example",
    )
    service = MagicMock(spec=GitHubCloneService)
    service.clone_project.return_value = project
    app.dependency_overrides[get_github_clone_service] = lambda: service

    response = client.post(
        "/projects/github",
        json={
            "name": "Example project",
            "description": "Description",
            "github_url": "https://github.com/openai/example",
        },
    )

    assert response.status_code == 201
    assert response.json()["source_type"] == "GITHUB"
    service.clone_project.assert_called_once()


def test_list_projects_endpoint(
    client: TestClient,
    project_factory: Callable[..., Project],
) -> None:
    projects = [project_factory(), project_factory(id=uuid.uuid4())]
    repository = MagicMock(spec=ProjectRepository)
    repository.get_all.return_value = projects
    app.dependency_overrides[get_project_repository] = lambda: repository

    response = client.get("/projects", params={"skip": 0, "limit": 10})

    assert response.status_code == 200
    assert response.json()["total"] == 2
    assert len(response.json()["items"]) == 2
    repository.get_all.assert_called_once_with(skip=0, limit=10)


def test_get_project_endpoint(
    client: TestClient,
    project_factory: Callable[..., Project],
) -> None:
    project = project_factory()
    repository = MagicMock(spec=ProjectRepository)
    repository.get_by_id.return_value = project
    app.dependency_overrides[get_project_repository] = lambda: repository

    response = client.get(f"/projects/{project.id}")

    assert response.status_code == 200
    assert response.json()["id"] == str(project.id)


def test_delete_project_endpoint(
    client: TestClient,
    project_factory: Callable[..., Project],
) -> None:
    project = project_factory()
    service = MagicMock(spec=ProjectDeletionService)
    service.delete_project.return_value = True
    app.dependency_overrides[get_project_deletion_service] = lambda: service

    response = client.delete(f"/projects/{project.id}")

    assert response.status_code == 204
    assert response.content == b""
    service.delete_project.assert_called_once_with(project.id)
