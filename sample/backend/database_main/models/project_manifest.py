"""Project Manifest ORM Model."""

import uuid
from datetime import datetime, timezone
from typing import Any, Optional

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from database_main.core.base import Base
from database_main.core.types import GUID, JsonDict


class ProjectManifest(Base):
    """Stores the generated project manifest and packaging metadata."""

    __tablename__ = "project_manifests"

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
    version: Mapped[str] = mapped_column(String(50), default="1.0.0")
    tech_stack: Mapped[str] = mapped_column(String(255), default="Python FastAPI / React")
    manifest_data: Mapped[Optional[Any]] = mapped_column(JsonDict(), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )
