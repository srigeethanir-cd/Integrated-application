import uuid

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.database.models.project import Project, ProjectStatus


class ProjectRepository:
    """Persistence operations for Project entities."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def create(self, project: Project) -> Project:
        self._session.add(project)
        self._commit_and_refresh(project)
        return project

    def get_by_id(
        self,
        project_id: uuid.UUID,
        *,
        for_update: bool = False,
    ) -> Project | None:
        if for_update:
            return self._session.get(Project, project_id, with_for_update=True)
        return self._session.get(Project, project_id)

    def get_all(self, skip: int = 0, limit: int = 100) -> list[Project]:
        statement = (
            select(Project)
            .order_by(Project.created_at.desc(), Project.id)
            .offset(skip)
            .limit(limit)
        )
        return list(self._session.scalars(statement).all())

    def update(self, project: Project) -> Project | None:
        existing_project = self.get_by_id(project.id)
        if existing_project is None:
            return None

        existing_project.name = project.name
        existing_project.description = project.description
        existing_project.source_type = project.source_type
        existing_project.github_url = project.github_url
        existing_project.storage_path = project.storage_path
        existing_project.status = project.status

        self._commit_and_refresh(existing_project)
        return existing_project

    def delete(
        self,
        project_id: uuid.UUID,
        *,
        commit: bool = True,
    ) -> Project | None:
        project = self.get_by_id(project_id)
        if project is None:
            return None

        self._session.delete(project)
        try:
            if commit:
                self._session.commit()
            else:
                self._session.flush()
        except SQLAlchemyError:
            self._session.rollback()
            raise

        return project

    def commit(self) -> None:
        try:
            self._session.commit()
        except SQLAlchemyError:
            self._session.rollback()
            raise

    def rollback(self) -> None:
        self._session.rollback()

    def update_status(
        self,
        project_id: uuid.UUID,
        status: ProjectStatus,
    ) -> Project | None:
        project = self.get_by_id(project_id)
        if project is None:
            return None

        project.status = status
        self._commit_and_refresh(project)
        return project

    def _commit_and_refresh(self, project: Project) -> None:
        try:
            self._session.flush()
            self._session.refresh(project)
            self._session.commit()
        except SQLAlchemyError:
            self._session.rollback()
            raise
