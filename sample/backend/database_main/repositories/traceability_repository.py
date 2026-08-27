"""Traceability repository — CRUD operations for the Traceability model."""

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from database_main.models.traceability import Traceability
from database_main.repositories.base_repository import BaseRepository


class TraceabilityRepository(BaseRepository[Traceability]):
    """Data-access layer for traceability records."""

    def __init__(self, db: Session) -> None:
        super().__init__(Traceability, db)

    def get_by_project(self, project_id: uuid.UUID, *, skip: int = 0, limit: int = 100) -> list[Traceability]:
        """Return all traceability records for a given project."""
        stmt = (
            select(Traceability)
            .where(Traceability.project_id == project_id)
            .offset(skip)
            .limit(limit)
        )
        return list(self.db.scalars(stmt).all())

    def get_by_source(self, source_id: uuid.UUID, *, skip: int = 0, limit: int = 100) -> list[Traceability]:
        """Return all traceability records matching a source ID."""
        stmt = (
            select(Traceability)
            .where(Traceability.source_id == source_id)
            .offset(skip)
            .limit(limit)
        )
        return list(self.db.scalars(stmt).all())

    def get_by_target(self, target_id: uuid.UUID, *, skip: int = 0, limit: int = 100) -> list[Traceability]:
        """Return all traceability records matching a target ID."""
        stmt = (
            select(Traceability)
            .where(Traceability.target_id == target_id)
            .offset(skip)
            .limit(limit)
        )
        return list(self.db.scalars(stmt).all())
