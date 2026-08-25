from __future__ import annotations

import uuid
from datetime import datetime
from enum import StrEnum
from typing import Any

from sqlalchemy import DateTime, Enum, Float, ForeignKey, Index, JSON, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class RuntimeValidationStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    PARTIAL = "partial"
    FAILED = "failed"


class RuntimeTestStatus(StrEnum):
    PASSED = "Passed"
    FAILED = "Failed"
    SKIPPED = "Skipped"
    NOT_EXECUTABLE = "NotExecutable"


class RuntimeValidationRun(Base):
    __tablename__ = "runtime_validation_runs"
    __table_args__ = (
        Index("ix_runtime_validation_runs_project_id", "project_id"),
        Index("ix_runtime_validation_runs_source_stage_run_id", "source_stage_run_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )
    source_stage_run_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("code_understanding_runs.id", ondelete="CASCADE"),
        nullable=False,
    )
    status: Mapped[RuntimeValidationStatus] = mapped_column(
        Enum(
            RuntimeValidationStatus,
            name="runtime_validation_status",
            values_callable=lambda enum: [item.value for item in enum],
        ),
        default=RuntimeValidationStatus.PENDING,
        server_default=RuntimeValidationStatus.PENDING.value,
        nullable=False,
    )
    execution_mode: Mapped[str] = mapped_column(
        String(50), default="managed", server_default="managed", nullable=False
    )
    base_url: Mapped[str] = mapped_column(String(2048), nullable=False)
    duration_ms: Mapped[float | None] = mapped_column(Float, nullable=True)
    summary: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    results: Mapped[list["RuntimeExecutionResult"]] = relationship(
        back_populates="run", cascade="all, delete-orphan", order_by="RuntimeExecutionResult.id"
    )


class RuntimeExecutionResult(Base):
    __tablename__ = "runtime_execution_results"
    __table_args__ = (
        Index("ix_runtime_execution_results_run_id", "run_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    run_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("runtime_validation_runs.id", ondelete="CASCADE"),
        nullable=False,
    )
    test_case_id: Mapped[str] = mapped_column(String(255), nullable=False)
    runtime_status: Mapped[RuntimeTestStatus] = mapped_column(
        Enum(
            RuntimeTestStatus,
            name="runtime_test_status",
            values_callable=lambda enum: [item.value for item in enum],
        ),
        nullable=False,
    )
    expected_result: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    actual_result: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    assertion_failure: Mapped[str | None] = mapped_column(Text)
    logs: Mapped[str | None] = mapped_column(Text)
    execution_time_ms: Mapped[float] = mapped_column(Float, default=0, nullable=False)
    run: Mapped[RuntimeValidationRun] = relationship(back_populates="results")
