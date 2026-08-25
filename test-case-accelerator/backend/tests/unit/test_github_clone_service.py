from pathlib import Path
from unittest.mock import MagicMock

import pytest
from git.exc import GitCommandError
from pytest_mock import MockerFixture

from app.database.models.project import ProjectSourceType, ProjectStatus
from app.database.repositories.project_repository import ProjectRepository
from app.services.ingestion.github_clone_service import (
    GitHubCloneError,
    GitHubCloneService,
)
from app.services.ingestion.storage_service import StorageService


def _service(tmp_path: Path) -> tuple[GitHubCloneService, MagicMock, StorageService]:
    repository = MagicMock(spec=ProjectRepository)
    repository.create.side_effect = lambda project: project
    storage = StorageService(tmp_path)
    return GitHubCloneService(repository, storage), repository, storage


def test_valid_github_url(tmp_path: Path, mocker: MockerFixture) -> None:
    service, repository, storage = _service(tmp_path)
    clone_from = mocker.patch(
        "app.services.ingestion.github_clone_service.Repo.clone_from"
    )

    project = service.clone_project("https://github.com/openai/example.git", "demo")

    assert project.github_url == "https://github.com/openai/example"
    assert project.source_type is ProjectSourceType.GITHUB
    assert project.status is ProjectStatus.UPLOADED
    assert project.storage_path == str(project.id)
    clone_from.assert_called_once_with(
        "https://github.com/openai/example",
        storage.get_project_directory(project.id) / "source",
        depth=1,
        single_branch=True,
        env={"GIT_TERMINAL_PROMPT": "0"},
    )
    repository.create.assert_called_once_with(project)


@pytest.mark.parametrize(
    "url",
    [
        "http://github.com/openai/example",
        "https://gitlab.com/openai/example",
        "https://github.com/openai",
        "https://user@github.com/openai/example",
    ],
)
def test_invalid_github_url(url: str, tmp_path: Path) -> None:
    service, repository, _ = _service(tmp_path)

    with pytest.raises(ValueError):
        service.clone_project(url, "demo")

    repository.create.assert_not_called()
    assert not list(tmp_path.iterdir())


def test_clone_failure(tmp_path: Path, mocker: MockerFixture) -> None:
    service, repository, _ = _service(tmp_path)
    mocker.patch(
        "app.services.ingestion.github_clone_service.Repo.clone_from",
        side_effect=GitCommandError("clone", 128),
    )

    with pytest.raises(GitHubCloneError):
        service.clone_project("https://github.com/openai/example", "demo")

    repository.create.assert_not_called()


def test_cleanup_on_clone_failure(tmp_path: Path, mocker: MockerFixture) -> None:
    service, _, storage = _service(tmp_path)
    mocker.patch(
        "app.services.ingestion.github_clone_service.Repo.clone_from",
        side_effect=GitCommandError("clone", 128),
    )

    with pytest.raises(GitHubCloneError):
        service.clone_project("https://github.com/openai/example", "demo")

    assert not any(storage.storage_root.iterdir())
