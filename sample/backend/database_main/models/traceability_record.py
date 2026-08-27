"""Traceability Record ORM Model."""

import uuid
from datetime import datetime, timezone
from typing import Any, Optional

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from database_main.core.base import Base
from database_main.core.types import GUID, JsonDict


class TraceabilityRecord(Base):
    """Tracks end-to-end traceability links between stories, components, APIs, and tests."""

    __tablename__ = "traceability_records"

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
    story_key: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    component_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    api_endpoint: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    db_table: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    test_case: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    details: Mapped[Optional[Any]] = mapped_column(JsonDict(), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )
