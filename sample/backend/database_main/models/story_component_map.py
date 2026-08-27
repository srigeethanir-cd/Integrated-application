"""StoryComponentMap ORM model.

Junction table that records which action (CREATE, MODIFY, DELETE, REUSE)
was performed on a component as a result of processing a story.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database_main.core.base import Base
from database_main.core.types import GUID


class StoryComponentMap(Base):
    """Maps a story to a component with an action type."""

    __tablename__ = "story_component_map"

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
    component_id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        ForeignKey("components.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    action: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        index=True,
        comment="One of: CREATE, MODIFY, DELETE, REUSE",
    )
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    # ── Relationships ───────────────────────────────────────────────────
    story: Mapped["Story"] = relationship(  # noqa: F821
        "Story", back_populates="story_component_maps",
    )
    component: Mapped["Component"] = relationship(  # noqa: F821
        "Component", back_populates="story_component_maps",
    )

    def __repr__(self) -> str:
        return f"<StoryComponentMap story={self.story_id!s} component={self.component_id!s} action={self.action!r}>"
