"""Traceability ORM model.

Tracks relationships between requirement sources, user stories, architecture blueprints,
generated components, and artifacts across AI agent executions.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship as rel

from app.database.base import Base
from app.database.types import GUID


class Traceability(Base):
    """Traceability record linking source elements to target artifacts."""

    __tablename__ = "traceability"

    trace_id: Mapped[uuid.UUID] = mapped_column(
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
    source_type: Mapped[str] = mapped_column(String(100), nullable=False)
    source_id: Mapped[uuid.UUID] = mapped_column(GUID(), nullable=False, index=True)
    relationship: Mapped[str] = mapped_column(String(100), nullable=False)
    target_type: Mapped[str] = mapped_column(String(100), nullable=False)
    target_id: Mapped[uuid.UUID] = mapped_column(GUID(), nullable=False, index=True)
    created_by_agent: Mapped[str | None] = mapped_column(String(100), nullable=True)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    # ── Backward Compatibility Properties ─────────────────────────────
    @property
    def id(self) -> uuid.UUID:
        return self.trace_id

    @id.setter
    def id(self, value: uuid.UUID) -> None:
        self.trace_id = value

    # ── Relationships ───────────────────────────────────────────────────
    project: Mapped["Project"] = rel(  # noqa: F821
        "Project", back_populates="traceability_records",
    )

    def __repr__(self) -> str:
        return f"<Traceability trace_id={self.trace_id!s} relationship={self.relationship!r}>"

