"""File repository — CRUD operations for the File model."""

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from database_main.models.file import File
from database_main.repositories.base_repository import BaseRepository


class FileRepository(BaseRepository[File]):
    """Data-access layer for generated files."""

    def __init__(self, db: Session) -> None:
        super().__init__(File, db)

    def get_by_component(self, component_id: uuid.UUID, *, skip: int = 0, limit: int = 100) -> list[File]:
        """Return all files belonging to a component."""
        stmt = (
            select(File)
            .where(File.component_id == component_id)
            .offset(skip)
            .limit(limit)
        )
        return list(self.db.scalars(stmt).all())

    def get_by_story(self, story_id: uuid.UUID, *, skip: int = 0, limit: int = 100) -> list[File]:
        """Return all files generated for a story."""
        stmt = (
            select(File)
            .where(File.story_id == story_id)
            .offset(skip)
            .limit(limit)
        )
        return list(self.db.scalars(stmt).all())

    def get_by_path(self, path: str) -> File | None:
        """Look up a file by its path."""
        stmt = select(File).where(File.path == path)
        return self.db.scalars(stmt).first()
