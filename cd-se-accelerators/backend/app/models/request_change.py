"""RequestChange SQLAlchemy ORM model."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Integer, Text, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from app.database.types import GUID


class RequestChange(Base):
    """Stores human-in-the-loop change requests for blueprint, stories, and files."""

    __tablename__ = "request_changes"

    request_change_id: Mapped[uuid.UUID] = mapped_column(
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
    blueprint_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID(),
        ForeignKey("blueprints.blueprint_id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    blueprint_version: Mapped[int | None] = mapped_column(Integer, nullable=True)
    location_type: Mapped[str] = mapped_column(String(100), nullable=False)  # blueprint, file_structure, tech_stack, etc.
    target_id: Mapped[str | None] = mapped_column(String(100), nullable=True)  # EPIC-002, US001, AC-01
    target_path: Mapped[str | None] = mapped_column(Text, nullable=True)  # backend/app/api/auth.py
    field_name: Mapped[str | None] = mapped_column(String(100), nullable=True)  # description, title, etc.
    original_value: Mapped[str | None] = mapped_column(Text, nullable=True)
    requested_change: Mapped[str] = mapped_column(Text, nullable=False)
    modified_prompt: Mapped[str | None] = mapped_column(Text, nullable=True)
    modified_value: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="PENDING")  # PENDING, PROCESSING, APPLIED, REJECTED, FAILED
    created_by: Mapped[str | None] = mapped_column(String(100), default="Business Analyst")
    
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

    # Relationships
    project: Mapped["Project"] = relationship("Project")  # noqa: F821
    blueprint: Mapped["Blueprint | None"] = relationship("Blueprint")  # noqa: F821

    def __repr__(self) -> str:
        return f"<RequestChange id={self.request_change_id!s} target={self.target_id or self.target_path} status={self.status}>"
