from collections.abc import Callable
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from sqlalchemy.exc import SQLAlchemyError

from app.database.models.project import Project
from app.database.repositories.project_repository import ProjectRepository
from app.services.ingestion.project_deletion_service import (
    ProjectDeletionError,
    ProjectDeletionService,
)
from app.services.ingestion.storage_service import StorageService


def _service(
    tmp_path: Path,
    project: Project,
) -> tuple[ProjectDeletionService, MagicMock, StorageService, Path]:
    repository = MagicMock(spec=ProjectRepository)
    repository.get_by_id.return_value = project
    repository.delete.return_value = project
    storage = StorageService(tmp_path)
    directory = storage.create_project_directory(project.id)
    (directory / "file.py").write_text("content", encoding="utf-8")
    return ProjectDeletionService(repository, storage), repository, storage, directory


def test_successful_delete(
    tmp_path: Path,
    project_factory: Callable[..., Project],
) -> None:
    project = project_factory()
    service, repository, _, directory = _service(tmp_path, project)

    assert service.delete_project(project.id) is True
    assert not directory.exists()
    assert not (tmp_path / f".deleting-{project.id}").exists()
    repository.delete.assert_called_once_with(project.id, commit=False)
    repository.commit.assert_called_once_with()
    repository.rollback.assert_not_called()


def test_restore_on_database_failure(
    tmp_path: Path,
    project_factory: Callable[..., Project],
) -> None:
    project = project_factory()
    service, repository, _, directory = _service(tmp_path, project)
    repository.delete.side_effect = SQLAlchemyError("database failure")

    with pytest.raises(SQLAlchemyError):
        service.delete_project(project.id)

    assert directory.is_dir()
    assert (directory / "file.py").is_file()
    repository.rollback.assert_called_once_with()
    repository.commit.assert_not_called()


def test_restore_on_filesystem_failure(
    tmp_path: Path,
    project_factory: Callable[..., Project],
) -> None:
    project = project_factory()
    service, repository, storage, directory = _service(tmp_path, project)
    storage.delete_staged_project_directory = MagicMock(
        side_effect=OSError("filesystem failure")
    )

    with pytest.raises(ProjectDeletionError):
        service.delete_project(project.id)

    assert directory.is_dir()
    assert (directory / "file.py").read_text(encoding="utf-8") == "content"
    repository.rollback.assert_called_once_with()
    repository.commit.assert_not_called()
    repository.create.assert_not_called()


def test_rollback_failure_is_recorded(
    tmp_path: Path,
    project_factory: Callable[..., Project],
) -> None:
    project = project_factory()
    service, repository, storage, _ = _service(tmp_path, project)
    storage.delete_staged_project_directory = MagicMock(
        side_effect=OSError("filesystem failure")
    )
    repository.rollback.side_effect = SQLAlchemyError("rollback failure")

    with pytest.raises(ProjectDeletionError) as captured:
        service.delete_project(project.id)

    assert captured.value.__cause__ is not None
    assert any(
        "database rollback failed" in note.lower()
        for note in captured.value.__cause__.__notes__
    )
