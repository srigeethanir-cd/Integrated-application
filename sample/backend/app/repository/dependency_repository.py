"""Dependency repository — CRUD operations for the Dependency model."""

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.dependency import Dependency
from app.repository.base_repository import BaseRepository


class DependencyRepository(BaseRepository[Dependency]):
    """Data-access layer for component dependency graph edges."""

    def __init__(self, db: Session) -> None:
        super().__init__(Dependency, db)

    def get_by_component(self, component_id: uuid.UUID) -> list[Dependency]:
        """Return outgoing dependency edges for a specific component."""
        stmt = select(Dependency).where(Dependency.component_id == component_id)
        return list(self.db.scalars(stmt).all())

    def get_by_components(self, component_ids: list[uuid.UUID]) -> list[Dependency]:
        """Return dependency edges where component_id or depends_on_component_id is in component_ids."""
        if not component_ids:
            return []
        stmt = select(Dependency).where(
            (Dependency.component_id.in_(component_ids))
            | (Dependency.depends_on_component_id.in_(component_ids))
        )
        return list(self.db.scalars(stmt).all())

    def get_by_project(self, project_id: uuid.UUID) -> list[Dependency]:
        """Return dependencies between components belonging to a project."""
        from app.models.component import Component

        stmt = (
            select(Dependency)
            .join(Component, Dependency.component_id == Component.id)
            .where(Component.project_id == project_id)
        )
        return list(self.db.scalars(stmt).all())
