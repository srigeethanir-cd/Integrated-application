"""Epic repository — CRUD operations for the Epic model."""

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from database_main.models.epic import Epic
from database_main.repositories.base_repository import BaseRepository


class EpicRepository(BaseRepository[Epic]):
    """Data-access layer for epics."""

    def __init__(self, db: Session) -> None:
        super().__init__(Epic, db)

    def get_by_project(self, project_id: uuid.UUID, *, skip: int = 0, limit: int = 100) -> list[Epic]:
        """Return all epics belonging to a project."""
        stmt = (
            select(Epic)
            .where(Epic.project_id == project_id)
            .offset(skip)
            .limit(limit)
        )
        return list(self.db.scalars(stmt).all())

    def get_by_blueprint(self, blueprint_id: uuid.UUID, *, skip: int = 0, limit: int = 100) -> list[Epic]:
        """Return all epics linked to a specific blueprint."""
        stmt = (
            select(Epic)
            .where(Epic.blueprint_id == blueprint_id)
            .offset(skip)
            .limit(limit)
        )
        return list(self.db.scalars(stmt).all())

    def get_by_key(self, epic_key: str) -> Epic | None:
        """Look up an epic by its unique key."""
        stmt = select(Epic).where(Epic.epic_key == epic_key)
        return self.db.scalars(stmt).first()
