"""Blueprint repository — CRUD operations for the Blueprint model."""

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.blueprint import Blueprint
from app.repository.base_repository import BaseRepository


class BlueprintRepository(BaseRepository[Blueprint]):
    """Data-access layer for blueprints."""

    def __init__(self, db: Session) -> None:
        super().__init__(Blueprint, db)

    def get_by_project(self, project_id: uuid.UUID, *, skip: int = 0, limit: int = 100) -> list[Blueprint]:
        """Return all blueprints for a given project."""
        stmt = (
            select(Blueprint)
            .where(Blueprint.project_id == project_id)
            .order_by(Blueprint.version.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(self.db.scalars(stmt).all())

    def get_latest_version(self, project_id: uuid.UUID) -> Blueprint | None:
        """Return the highest-version blueprint for a project."""
        stmt = (
            select(Blueprint)
            .where(Blueprint.project_id == project_id)
            .order_by(Blueprint.version.desc())
            .limit(1)
        )
        return self.db.scalars(stmt).first()

