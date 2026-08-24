"""GenerationHistory ORM model.

Audit trail recording every action taken by an AI agent for a story.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from app.database.types import GUID


class GenerationHistory(Base):
    """An audit record for agent actions on a story."""

    __tablename__ = "generation_history"

    id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        primary_key=True,
        default=uuid.uuid4,
    )
    story_id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        ForeignKey("user_stories.story_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    agent: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    action: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    execution_time: Mapped[float | None] = mapped_column(Float, nullable=True)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    # ── Relationships ───────────────────────────────────────────────────
    story: Mapped["Story"] = relationship(  # noqa: F821
        "Story", back_populates="generation_histories",
    )

    def __repr__(self) -> str:
        return f"<GenerationHistory id={self.id!s} agent={self.agent!r} status={self.status!r}>"
