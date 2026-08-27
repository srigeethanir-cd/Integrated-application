"""GenerationHistory repository — CRUD operations for the GenerationHistory model."""

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.generation_history import GenerationHistory
from app.repository.base_repository import BaseRepository


class GenerationHistoryRepository(BaseRepository[GenerationHistory]):
    """Data-access layer for generation history audit trail records."""

    def __init__(self, db: Session) -> None:
        super().__init__(GenerationHistory, db)

    def get_by_story(
        self, story_id: uuid.UUID, *, skip: int = 0, limit: int = 100
    ) -> list[GenerationHistory]:
        """Return all generation history audit records for a user story."""
        stmt = (
            select(GenerationHistory)
            .where(GenerationHistory.story_id == story_id)
            .order_by(GenerationHistory.timestamp.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(self.db.scalars(stmt).all())

    def get_by_agent(
        self, agent_name: str, *, skip: int = 0, limit: int = 100
    ) -> list[GenerationHistory]:
        """Return audit history records filtered by agent name."""
        stmt = (
            select(GenerationHistory)
            .where(GenerationHistory.agent == agent_name)
            .order_by(GenerationHistory.timestamp.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(self.db.scalars(stmt).all())
