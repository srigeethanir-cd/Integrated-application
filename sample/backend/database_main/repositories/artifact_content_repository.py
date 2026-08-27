"""ArtifactContent repository — CRUD operations for the ArtifactContent model."""

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from database_main.models.artifact_content import ArtifactContent
from database_main.repositories.base_repository import BaseRepository


class ArtifactContentRepository(BaseRepository[ArtifactContent]):
    """Data-access layer for artifact contents."""

    def __init__(self, db: Session) -> None:
        super().__init__(ArtifactContent, db)

    def get_by_artifact(self, artifact_id: uuid.UUID, *, skip: int = 0, limit: int = 100) -> list[ArtifactContent]:
        """Return all content versions/files belonging to an artifact."""
        stmt = (
            select(ArtifactContent)
            .where(ArtifactContent.artifact_id == artifact_id)
            .offset(skip)
            .limit(limit)
        )
        return list(self.db.scalars(stmt).all())
