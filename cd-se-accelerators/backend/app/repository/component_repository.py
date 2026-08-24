"""Component repository — CRUD operations for the Component model."""

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.component import Component
from app.repository.base_repository import BaseRepository


class ComponentRepository(BaseRepository[Component]):
    """Data-access layer for components."""

    def __init__(self, db: Session) -> None:
        super().__init__(Component, db)

    def get_by_project(self, project_id: uuid.UUID, *, skip: int = 0, limit: int = 100) -> list[Component]:
        """Return all components for a given project."""
        stmt = (
            select(Component)
            .where(Component.project_id == project_id)
            .offset(skip)
            .limit(limit)
        )
        return list(self.db.scalars(stmt).all())

    def get_by_type(self, component_type: str, *, skip: int = 0, limit: int = 100) -> list[Component]:
        """Return components filtered by type."""
        stmt = (
            select(Component)
            .where(Component.type == component_type)
            .offset(skip)
            .limit(limit)
        )
        return list(self.db.scalars(stmt).all())

    def get_by_agent(self, agent_name: str, *, skip: int = 0, limit: int = 100) -> list[Component]:
        """Return components created by a specific agent."""
        stmt = (
            select(Component)
            .where(Component.created_by_agent == agent_name)
            .offset(skip)
            .limit(limit)
        )
        return list(self.db.scalars(stmt).all())
