"""Artifact repository — CRUD operations for the Artifact model."""

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from database_main.models.artifact import Artifact
from database_main.repositories.base_repository import BaseRepository


class ArtifactRepository(BaseRepository[Artifact]):
    """Data-access layer for generated artifacts."""

    def __init__(self, db: Session) -> None:
        super().__init__(Artifact, db)

    def get_by_project(self, project_id: uuid.UUID, *, skip: int = 0, limit: int = 100) -> list[Artifact]:
        """Return all artifacts for a given project."""
        stmt = (
            select(Artifact)
            .where(Artifact.project_id == project_id)
            .offset(skip)
            .limit(limit)
        )
        return list(self.db.scalars(stmt).all())

    def get_by_story(self, story_id: uuid.UUID, *, skip: int = 0, limit: int = 100) -> list[Artifact]:
        """Return all artifacts associated with a user story."""
        stmt = (
            select(Artifact)
            .where(Artifact.story_id == story_id)
            .offset(skip)
            .limit(limit)
        )
        return list(self.db.scalars(stmt).all())
