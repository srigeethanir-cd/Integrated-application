"""Story repository — CRUD operations for the Story model."""

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from database_main.models.story import Story
from database_main.repositories.base_repository import BaseRepository


class StoryRepository(BaseRepository[Story]):
    """Data-access layer for stories."""

    def __init__(self, db: Session) -> None:
        super().__init__(Story, db)

    def get_by_project(self, project_id: uuid.UUID, *, skip: int = 0, limit: int = 100) -> list[Story]:
        """Return all stories belonging to a project."""
        stmt = (
            select(Story)
            .where(Story.project_id == project_id)
            .offset(skip)
            .limit(limit)
        )
        return list(self.db.scalars(stmt).all())

    def get_by_epic(self, epic_id: uuid.UUID, *, skip: int = 0, limit: int = 100) -> list[Story]:
        """Return all stories belonging to an epic."""
        stmt = (
            select(Story)
            .where(Story.epic_id == epic_id)
            .offset(skip)
            .limit(limit)
        )
        return list(self.db.scalars(stmt).all())

    def get_by_key(self, story_key: str) -> Story | None:
        """Look up a story by its unique key."""
        stmt = select(Story).where(Story.story_key == story_key)
        return self.db.scalars(stmt).first()

    def get_by_status(self, status: str, *, skip: int = 0, limit: int = 100) -> list[Story]:
        """Return stories filtered by status."""
        stmt = (
            select(Story)
            .where(Story.approval_status == status)
            .offset(skip)
            .limit(limit)
        )
        return list(self.db.scalars(stmt).all())

    def approve(self, story_id: uuid.UUID) -> Story | None:
        """Mark a story as approved."""
        db_obj = self.get(story_id)
        if not db_obj:
            return None
        return self.update(db_obj, {"approval_status": "approved"})

