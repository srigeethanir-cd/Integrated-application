"""Epic ORM model.

An epic groups related user stories under a project and blueprint.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from app.database.types import GUID


class Epic(Base):
    """An epic grouping user stories for a project."""

    __tablename__ = "epics"
    __table_args__ = (
        # epic_key must be unique within a project, but can repeat across projects
        UniqueConstraint("project_id", "epic_key", name="uq_epics_project_epic_key"),
    )

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
    blueprint_id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        ForeignKey("blueprints.blueprint_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    epic_key: Mapped[str] = mapped_column(String(50), nullable=False, index=True)

    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    priority: Mapped[str | None] = mapped_column(String(20), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    # ── Relationships ───────────────────────────────────────────────────
    project: Mapped["Project"] = relationship(  # noqa: F821
        "Project", back_populates="epics",
    )
    blueprint: Mapped["Blueprint"] = relationship(  # noqa: F821
        "Blueprint", back_populates="epics",
    )
    stories: Mapped[list["Story"]] = relationship(  # noqa: F821
        "Story", back_populates="epic", cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Epic id={self.id!s} key={self.epic_key!r}>"
