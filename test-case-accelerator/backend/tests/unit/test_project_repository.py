import uuid
from collections.abc import Callable
from unittest.mock import MagicMock

from sqlalchemy.orm import Session

from app.database.models.project import Project, ProjectStatus
from app.database.repositories.project_repository import ProjectRepository


def test_create_project(project_factory: Callable[..., Project]) -> None:
    session = MagicMock(spec=Session)
    repository = ProjectRepository(session)
    project = project_factory()

    result = repository.create(project)

    assert result is project
    session.add.assert_called_once_with(project)
    session.flush.assert_called_once_with()
    session.refresh.assert_called_once_with(project)
    session.commit.assert_called_once_with()


def test_get_project_by_id(project_factory: Callable[..., Project]) -> None:
    session = MagicMock(spec=Session)
    repository = ProjectRepository(session)
    project = project_factory()
    session.get.return_value = project

    result = repository.get_by_id(project.id)

    assert result is project
    session.get.assert_called_once_with(Project, project.id)


def test_get_all_projects(project_factory: Callable[..., Project]) -> None:
    session = MagicMock(spec=Session)
    repository = ProjectRepository(session)
    projects = [project_factory(), project_factory(id=uuid.uuid4())]
    session.scalars.return_value.all.return_value = projects

    result = repository.get_all(skip=10, limit=20)

    assert result == projects
    session.scalars.assert_called_once()


def test_update_project_status(project_factory: Callable[..., Project]) -> None:
    session = MagicMock(spec=Session)
    repository = ProjectRepository(session)
    project = project_factory()
    session.get.return_value = project

    result = repository.update_status(project.id, ProjectStatus.READY)

    assert result is project
    assert project.status is ProjectStatus.READY
    session.flush.assert_called_once_with()
    session.refresh.assert_called_once_with(project)
    session.commit.assert_called_once_with()


def test_delete_project(project_factory: Callable[..., Project]) -> None:
    session = MagicMock(spec=Session)
    repository = ProjectRepository(session)
    project = project_factory()
    session.get.return_value = project

    result = repository.delete(project.id)

    assert result is project
    session.delete.assert_called_once_with(project)
    session.commit.assert_called_once_with()


def test_delete_project_without_commit(
    project_factory: Callable[..., Project],
) -> None:
    session = MagicMock(spec=Session)
    repository = ProjectRepository(session)
    project = project_factory()
    session.get.return_value = project

    result = repository.delete(project.id, commit=False)

    assert result is project
    session.delete.assert_called_once_with(project)
    session.flush.assert_called_once_with()
    session.commit.assert_not_called()


def test_transaction_controls() -> None:
    session = MagicMock(spec=Session)
    repository = ProjectRepository(session)

    repository.commit()
    repository.rollback()

    session.commit.assert_called_once_with()
    session.rollback.assert_called_once_with()
