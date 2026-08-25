"""SQLAlchemy model for Stage 3 code-understanding runs."""

from __future__ import annotations

import uuid
from datetime import datetime
from enum import StrEnum
from typing import Any

from sqlalchemy import DateTime, Enum, ForeignKey, Index, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class CodeUnderstandingStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class CodeUnderstandingRun(Base):
    """Persisted execution and structured result of a Stage 3 analysis."""

    __tablename__ = "code_understanding_runs"
    __table_args__ = (
        Index("ix_code_understanding_runs_project_id", "project_id"),
        Index(
            "ix_code_understanding_runs_dependency_run_id",
            "dependency_run_id",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
    )
    dependency_run_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("dependency_runs.id", ondelete="CASCADE"),
        nullable=False,
    )
    status: Mapped[CodeUnderstandingStatus] = mapped_column(
        Enum(
            CodeUnderstandingStatus,
            name="code_understanding_status",
            values_callable=lambda status: [item.value for item in status],
        ),
        nullable=False,
        default=CodeUnderstandingStatus.PENDING,
        server_default=CodeUnderstandingStatus.PENDING.value,
    )
    result: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    model_name: Mapped[str] = mapped_column(String(255), nullable=False)
    prompt_version: Mapped[str] = mapped_column(String(100), nullable=False)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    failed_stage: Mapped[str | None] = mapped_column(String(100), nullable=True)
    failure_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    retry_count: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )
    last_successful_stage: Mapped[str | None] = mapped_column(
        String(100), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    finished_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
