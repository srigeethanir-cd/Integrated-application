"""Project ORM model.

Represents the top-level entity that owns blueprints, epics, and
components within the BA Accelerator pipeline.
"""

import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship, foreign

from database_main.core.base import Base
from database_main.core.types import GUID, JsonDict


class Project(Base):
    """A generated software project driven by user stories."""

    __tablename__ = "projects"

    project_id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        primary_key=True,
        default=uuid.uuid4,
    )
    project_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    tech_stack: Mapped[Any | None] = mapped_column(JsonDict(), nullable=True)
    requirements_json: Mapped[Any | None] = mapped_column(JsonDict(), nullable=True)
    approval_mode: Mapped[str] = mapped_column(String(50), nullable=False, default="HUMAN_IN_LOOP")
    # ── Normalized Dynamic Project Status Aggregation ───────────────────
    @property
    def status(self) -> str:
        if not self.stories:
            return "ACTIVE"
        
        gen_stats = [s.generation_status for s in self.stories]
        val_stats = [s.validation_status for s in self.stories]
        app_stats = [s.approval_status for s in self.stories]
        merge_stats = [s.merge_status for s in self.stories]

        if all(m == "MERGED" for m in merge_stats):
            return "EXPORT_READY"
        if any(m == "MERGED" for m in merge_stats):
            return "PROJECT_VALIDATED"
        if all(a == "approved" for a in app_stats):
            return "READY_TO_MERGE"
        if any(a == "rejected" for a in app_stats):
            return "REJECTED_BY_BA"
        if any(a == "approved" for a in app_stats):
            return "PAUSED_FOR_HUMAN_APPROVAL"
        if any(g == "GENERATING" for g in gen_stats):
            return "GENERATING"
        if all(g == "GENERATED" for g in gen_stats):
            if any(v == "FAILED" for v in val_stats):
                return "VALIDATION_FAILED"
            if all(v == "VALIDATED" for v in val_stats):
                return "PAUSED_FOR_HUMAN_APPROVAL"
            return "VALIDATION_PENDING"
        
        return "RUNNING_STAGE_1"

    @status.setter
    def status(self, value: str) -> None:
        pass
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
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

    # ── Backward Compatibility Properties ─────────────────────────────
    @property
    def id(self) -> uuid.UUID:
        return self.project_id

    @id.setter
    def id(self, value: uuid.UUID) -> None:
        self.project_id = value

    @property
    def name(self) -> str:
        return self.project_name

    @name.setter
    def name(self, value: str) -> None:
        self.project_name = value

    # ── Relationships ───────────────────────────────────────────────────
    blueprints: Mapped[list["Blueprint"]] = relationship(  # noqa: F821
        "Blueprint", back_populates="project", cascade="all, delete-orphan",
    )
    epics: Mapped[list["Epic"]] = relationship(  # noqa: F821
        "Epic", back_populates="project", cascade="all, delete-orphan",
    )
    components: Mapped[list["Component"]] = relationship(  # noqa: F821
        "Component", back_populates="project", cascade="all, delete-orphan",
    )
    stories: Mapped[list["Story"]] = relationship(  # noqa: F821
        "Story", back_populates="project", cascade="all, delete-orphan",
    )
    traceability_records: Mapped[list["Traceability"]] = relationship(  # noqa: F821
        "Traceability", back_populates="project", cascade="all, delete-orphan",
    )
    artifacts: Mapped[list["Artifact"]] = relationship(  # noqa: F821
        "Artifact",
        primaryjoin="Project.project_id == Artifact.project_id",
        foreign_keys="Artifact.project_id",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Project project_id={self.project_id!s} project_name={self.project_name!r}>"

