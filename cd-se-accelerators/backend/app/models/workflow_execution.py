import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import DateTime, String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base
from app.database.types import JsonDict, GUID


class WorkflowExecutionSession(Base):
    """Stores the execution state of workflows to replace in-memory dictionaries."""

    __tablename__ = "workflow_execution_sessions"

    execution_id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        ForeignKey("projects.project_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    workflow_id: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )
    current_step: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        default="NOT_STARTED",
    )
    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="NOT_STARTED",
    )
    execution_state: Mapped[Any | None] = mapped_column(
        JsonDict(),
        nullable=False,
        default=dict,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    def __repr__(self) -> str:
        return f"<WorkflowExecutionSession execution_id={self.execution_id} project_id={self.project_id} status={self.status}>"
