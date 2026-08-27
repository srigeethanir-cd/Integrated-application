"""Story ORM model.

A user story is the atomic unit of work fed to the AI agents.
Acceptance criteria are stored as JSONB for flexible structure.
"""

import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database_main.core.base import Base
from database_main.core.types import GUID, JsonDict


def _get_timestamp(dt: datetime | None) -> float:
    if dt is None:
        return 0.0
    if dt.tzinfo is not None:
        return dt.timestamp()
    return dt.replace(tzinfo=timezone.utc).timestamp()




class Story(Base):
    """A single user story belonging to a project (and optionally an epic)."""

    __tablename__ = "user_stories"
    __table_args__ = (
        UniqueConstraint("project_id", "story_key", name="uq_user_stories_project_story_key"),
    )

    story_id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        primary_key=True,
        default=uuid.uuid4,
    )
    project_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID(),
        ForeignKey("projects.project_id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )

    epic_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID(),
        ForeignKey("epics.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    story_key: Mapped[str | None] = mapped_column(String(50), nullable=True, index=True)
    story_title: Mapped[str] = mapped_column(String(500), nullable=False)
    story_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    acceptance_criteria: Mapped[Any | None] = mapped_column(JsonDict(), nullable=True)
    # ── Normalized Properties (Backward Compatibility) ───────────────────
    @property
    def approval_status(self) -> str:
        if self.lifecycle_records:
            app_records = [
                rec for rec in self.lifecycle_records 
                if (str(rec.decision or "").upper() in ("APPROVED", "REJECTED", "ACCEPTED") or 
                    str(rec.status or "").upper() in ("APPROVED", "REJECTED", "ACCEPTED"))
            ]
            if app_records:
                latest = sorted(app_records, key=lambda x: _get_timestamp(getattr(x, "created_at", None)))[-1]
                dec = str(latest.decision or "").upper()
                stat = str(latest.status or "").upper()
                return dec if dec in ("APPROVED", "REJECTED", "ACCEPTED") else stat
        return "PENDING"

    @approval_status.setter
    def approval_status(self, value: str) -> None:
        from database_main.models.consolidated_models import StoryLifecycle
        self.lifecycle_records.append(StoryLifecycle(
            status=value.upper(),
            decision=value.upper(),
            reviewer="Business Analyst",
            comments="Status updated.",
            version=self.version
        ))

    @property
    def generation_status(self) -> str:
        if self.lifecycle_records:
            gen_records = [rec for rec in self.lifecycle_records if rec.status in ("DRAFT", "GENERATING", "GENERATED", "COMPLETED", "FAILED")]
            if gen_records:
                latest = sorted(gen_records, key=lambda x: _get_timestamp(getattr(x, "created_at", None)))[-1]
                return latest.status
        return "DRAFT"

    @generation_status.setter
    def generation_status(self, value: str) -> None:
        from database_main.models.consolidated_models import StoryLifecycle
        self.lifecycle_records.append(StoryLifecycle(
            status=value.upper(),
            version=self.version
        ))

    @property
    def validation_status(self) -> str:
        if self.lifecycle_records:
            val_records = [rec for rec in self.lifecycle_records if rec.status in ("VALIDATED", "PASSED", "FAILED") or rec.validation_type]
            if val_records:
                latest = sorted(val_records, key=lambda x: _get_timestamp(getattr(x, "created_at", None)))[-1]
                return latest.status
        return "PENDING"

    @validation_status.setter
    def validation_status(self, value: str) -> None:
        from database_main.models.consolidated_models import StoryLifecycle
        self.lifecycle_records.append(StoryLifecycle(
            status=value.upper(),
            validation_type="story",
            report={}
        ))

    @property
    def preview_status(self) -> str:
        if self.generation_status in ("GENERATED", "VALIDATED", "PREVIEW_READY"):
            return "PREVIEW_READY"
        return "PENDING"

    @preview_status.setter
    def preview_status(self, value: str) -> None:
        pass

    @property
    def merge_status(self) -> str:
        if self.merges:
            latest = sorted(self.merges, key=lambda x: _get_timestamp(x.created_at))[-1]
            return latest.status
        return "PENDING"

    @merge_status.setter
    def merge_status(self, value: str) -> None:
        from database_main.models import StoryMerge
        self.merges.append(StoryMerge(
            status=value,
            merged_files=[]
        ))

    @property
    def export_status(self) -> str:
        if self.merge_status == "MERGED":
            return "EXPORT_READY"
        return "PENDING"

    @export_status.setter
    def export_status(self, value: str) -> None:
        pass

    @property
    def version(self) -> int:
        if self.executions:
            latest = sorted(self.executions, key=lambda x: _get_timestamp(x.created_at))[-1]
            return latest.version
        return 1

    @version.setter
    def version(self, value: int) -> None:
        pass

    @property
    def retry_count(self) -> int:
        if self.executions:
            latest = sorted(self.executions, key=lambda x: _get_timestamp(x.created_at))[-1]
            return latest.retry_count
        return 0

    @retry_count.setter
    def retry_count(self, value: int) -> None:
        pass

    @property
    def assigned_agent(self) -> str:
        if self.executions:
            latest = sorted(self.executions, key=lambda x: _get_timestamp(x.created_at))[-1]
            return latest.assigned_agent
        return "Agent2"

    @assigned_agent.setter
    def assigned_agent(self, value: str) -> None:
        pass

    @property
    def execution_timestamp(self) -> datetime | None:
        if self.executions:
            latest = sorted(self.executions, key=lambda x: _get_timestamp(x.created_at))[-1]
            return latest.start_time
        return None

    @execution_timestamp.setter
    def execution_timestamp(self, value: datetime | None) -> None:
        pass

    @property
    def audit_trail(self) -> dict | None:
        if self.audits:
            events = []
            for a in sorted(self.audits, key=lambda x: _get_timestamp(x.timestamp)):
                events.append({
                    "timestamp": a.timestamp.isoformat(),
                    "event": f"State transitioned from {a.previous_state} to {a.new_state}. User: {a.user}. Comments: {a.comments}"
                })
            return {"events": events}
        return {"events": []}

    @audit_trail.setter
    def audit_trail(self, value: dict | None) -> None:
        pass
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    # ── Backward Compatibility Properties ─────────────────────────────
    @property
    def id(self) -> uuid.UUID:
        return self.story_id

    @id.setter
    def id(self, value: uuid.UUID) -> None:
        self.story_id = value

    @property
    def title(self) -> str:
        return self.story_title

    @title.setter
    def title(self, value: str) -> None:
        self.story_title = value

    @property
    def description(self) -> str | None:
        return self.story_description

    @description.setter
    def description(self, value: str | None) -> None:
        self.story_description = value

    @property
    def status(self) -> str:
        return self.approval_status

    @status.setter
    def status(self, value: str) -> None:
        self.approval_status = value

    @property
    def approved(self) -> bool:
        return self.approval_status.lower() in ("approved", "true")

    @approved.setter
    def approved(self, value: bool) -> None:
        self.approval_status = "approved" if value else "pending"

    # ── Relationships ───────────────────────────────────────────────────
    project: Mapped["Project"] = relationship(  # noqa: F821
        "Project", back_populates="stories",
    )
    epic: Mapped["Epic | None"] = relationship(  # noqa: F821
        "Epic", back_populates="stories",
    )
    # ── Primary owning relationships (cascade lives here) ──────────────
    files: Mapped[list["GeneratedFile"]] = relationship(  # noqa: F821
        "GeneratedFile", back_populates="story", cascade="all, delete-orphan",
    )
    # Alias – read-only so SQLAlchemy uses a single mapper relationship
    generated_files: Mapped[list["GeneratedFile"]] = relationship(  # noqa: F821
        "GeneratedFile", viewonly=True,
    )
    artifacts: Mapped[list["Artifact"]] = relationship(  # noqa: F821
        "Artifact", back_populates="story", cascade="all, delete-orphan",
    )
    # Alias – read-only
    consolidated_artifacts: Mapped[list["Artifact"]] = relationship(  # noqa: F821
        "Artifact", viewonly=True,
    )
    story_component_maps: Mapped[list["StoryComponentMap"]] = relationship(  # noqa: F821
        "StoryComponentMap", back_populates="story", cascade="all, delete-orphan",
    )
    generation_histories: Mapped[list["GenerationHistory"]] = relationship(  # noqa: F821
        "GenerationHistory", back_populates="story", cascade="all, delete-orphan",
    )
    validation_results: Mapped[list["ProjectValidation"]] = relationship(  # noqa: F821
        "ProjectValidation", back_populates="story", cascade="all, delete-orphan",
    )
    # Alias – read-only
    validation_records: Mapped[list["ProjectValidation"]] = relationship(  # noqa: F821
        "ProjectValidation", viewonly=True,
    )
    dependencies: Mapped[list["StoryDependency"]] = relationship(  # noqa: F821
        "StoryDependency", back_populates="story", cascade="all, delete-orphan",
    )

    # ── Lifecycle relationships (single owning, rest are viewonly aliases) ──
    lifecycle_records: Mapped[list["StoryLifecycle"]] = relationship(
        "StoryLifecycle", back_populates="story", cascade="all, delete-orphan",
    )
    # Viewonly aliases that filter locally — avoids duplicate mapper conflict
    executions: Mapped[list["StoryLifecycle"]] = relationship(
        "StoryLifecycle", viewonly=True,
    )
    validations: Mapped[list["StoryLifecycle"]] = relationship(
        "StoryLifecycle", viewonly=True,
    )
    approvals: Mapped[list["StoryLifecycle"]] = relationship(
        "StoryLifecycle", viewonly=True,
    )
    merges: Mapped[list["StoryLifecycle"]] = relationship(
        "StoryLifecycle", viewonly=True,
    )

    # ── History relationships (single owning, rest are viewonly aliases) ───
    history_records: Mapped[list["StoryHistory"]] = relationship(
        "StoryHistory", back_populates="story", cascade="all, delete-orphan",
    )
    # Viewonly aliases
    versions: Mapped[list["StoryHistory"]] = relationship(
        "StoryHistory", viewonly=True,
    )
    audits: Mapped[list["StoryHistory"]] = relationship(
        "StoryHistory", viewonly=True,
    )

    def __repr__(self) -> str:
        return f"<Story story_id={self.story_id!s} title={self.story_title!r} status={self.approval_status!r}>"

