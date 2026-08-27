"""Project repository — CRUD operations for the Project model."""

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from database_main.models.project import Project
from database_main.repositories.base_repository import BaseRepository


class ProjectRepository(BaseRepository[Project]):
    """Data-access layer for projects."""

    def __init__(self, db: Session) -> None:
        super().__init__(Project, db)

    def get_by_name(self, name: str) -> Project | None:
        """Look up a project by its exact name."""
        stmt = select(Project).where(Project.name == name)
        return self.db.scalars(stmt).first()

    def get_by_status(self, status: str, *, skip: int = 0, limit: int = 100) -> list[Project]:
        """Return projects filtered by status."""
        stmt = (
            select(Project)
            .where(Project.status == status)
            .offset(skip)
            .limit(limit)
        )
        return list(self.db.scalars(stmt).all())

    def update_status(self, project_id: uuid.UUID, status: str) -> Project | None:
        """Convenience method to update only the status field."""
        db_obj = self.get(project_id)
        if not db_obj:
            return None
        return self.update(db_obj, {"status": status})
