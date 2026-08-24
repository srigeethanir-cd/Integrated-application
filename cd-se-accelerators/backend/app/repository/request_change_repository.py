"""RequestChange repository — CRUD operations for the RequestChange model."""

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.request_change import RequestChange
from app.repository.base_repository import BaseRepository


class RequestChangeRepository(BaseRepository[RequestChange]):
    """Data-access layer for request changes."""

    def __init__(self, db: Session) -> None:
        super().__init__(RequestChange, db)

    def get_by_project(self, project_id: uuid.UUID, *, skip: int = 0, limit: int = 100) -> list[RequestChange]:
        """Return all request changes for a given project."""
        stmt = (
            select(RequestChange)
            .where(RequestChange.project_id == project_id)
            .order_by(RequestChange.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(self.db.scalars(stmt).all())
