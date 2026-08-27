"""Pipeline State ORM Model."""

import uuid
from datetime import datetime, timezone
from typing import Any, Optional

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from database_main.core.base import Base
from database_main.core.types import GUID, JsonDict


class PipelineState(Base):
    """Tracks the live pipeline state across Agent 0 through Agent 3."""

    __tablename__ = "pipeline_states"

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
    current_stage: Mapped[str] = mapped_column(String(100), default="NOT_STARTED")
    status: Mapped[str] = mapped_column(String(50), default="PENDING")
    progress_percentage: Mapped[int] = mapped_column(Integer, default=0)
    stage_data: Mapped[Optional[Any]] = mapped_column(JsonDict(), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
