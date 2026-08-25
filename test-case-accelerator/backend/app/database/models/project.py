from __future__ import annotations

import uuid
from datetime import datetime
from enum import StrEnum
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base

if TYPE_CHECKING:
    from app.database.models.dependency import DependencyRun
    from app.database.models.security_scan import SecurityScanRun


class ProjectStatus(StrEnum):
    UPLOADED = "UPLOADED"
    PROCESSING = "PROCESSING"
    READY = "READY"
    FAILED = "FAILED"


class ProjectSourceType(StrEnum):
    ZIP = "ZIP"
    GITHUB = "GITHUB"


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    source_type: Mapped[ProjectSourceType] = mapped_column(
        Enum(ProjectSourceType, name="project_source_type"),
        nullable=False,
    )
    github_url: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    storage_path: Mapped[str] = mapped_column(String(1024), nullable=False)
    status: Mapped[ProjectStatus] = mapped_column(
        Enum(ProjectStatus, name="project_status"),
        nullable=False,
        default=ProjectStatus.UPLOADED,
        server_default=ProjectStatus.UPLOADED.value,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )
    dependency_runs: Mapped[list[DependencyRun]] = relationship(
        back_populates="project",
        cascade="all, delete-orphan",
    )
    security_scan_runs: Mapped[list[SecurityScanRun]] = relationship(
        back_populates="project",
        cascade="all, delete-orphan",
    )
