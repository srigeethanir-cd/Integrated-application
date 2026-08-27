"""Component ORM model.

A component represents a logical unit of the generated application
(e.g. a service, module, or UI component) created by one of the AI agents.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database_main.core.base import Base
from database_main.core.types import GUID


class Component(Base):
    """A logical component of the generated application."""

    __tablename__ = "components"

    id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        primary_key=True,
        default=uuid.uuid4,
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        ForeignKey("projects.project_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    path: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by_agent: Mapped[str | None] = mapped_column(String(50), nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    # ── Relationships ───────────────────────────────────────────────────
    project: Mapped["Project"] = relationship(  # noqa: F821
        "Project", back_populates="components",
    )
    files: Mapped[list["GeneratedFile"]] = relationship(  # noqa: F821
        "GeneratedFile", back_populates="component", cascade="all, delete-orphan",
    )
    story_component_maps: Mapped[list["StoryComponentMap"]] = relationship(  # noqa: F821
        "StoryComponentMap", back_populates="component", cascade="all, delete-orphan",
    )
    # Outgoing dependency edges (this component depends on others)
    dependencies_out: Mapped[list["StoryDependency"]] = relationship(  # noqa: F821
        "StoryDependency",
        foreign_keys="StoryDependency.component_id",
        back_populates="component",
        cascade="all, delete-orphan",
    )
    # Incoming dependency edges (other components depend on this one)
    dependencies_in: Mapped[list["StoryDependency"]] = relationship(  # noqa: F821
        "StoryDependency",
        foreign_keys="StoryDependency.depends_on_component_id",
        back_populates="depends_on_component",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Component id={self.id!s} name={self.name!r} type={self.type!r}>"
