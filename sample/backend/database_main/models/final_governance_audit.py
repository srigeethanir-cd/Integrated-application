import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import DateTime, String, Text, Column, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from database_main.core.base import Base
from database_main.core.types import JsonDict, GUID


class FinalGovernanceAudit(Base):
    """Stores final governance review checkpoints and history records."""

    __tablename__ = "final_governance_audits"

    id: Mapped[str] = mapped_column(
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
    story_id: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )
    action: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )
    reviewer: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    comments: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    # Map Python attribute name metadata_json to DB column named metadata to avoid Base.metadata conflict
    metadata_json = Column(
        "metadata",
        JsonDict(),
        nullable=False,
        default=dict,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    def __repr__(self) -> str:
        return f"<FinalGovernanceAudit id={self.id} project_id={self.project_id} status={self.status}>"
