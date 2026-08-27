"""Blueprint ORM model.

Stores a versioned architecture blueprint for a project, including
JSONB columns for structured sub-blueprints (folder structure,
API contracts, workflow, shared components).
"""

import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import DateTime, ForeignKey, Integer, Text, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database_main.core.base import Base
from database_main.core.types import GUID, JsonDict


class Blueprint(Base):
    """A versioned architecture blueprint belonging to a project."""

    __tablename__ = "blueprints"

    blueprint_id: Mapped[uuid.UUID] = mapped_column(
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
    architecture: Mapped[str | None] = mapped_column(Text, nullable=True)
    folder_structure: Mapped[Any | None] = mapped_column(JsonDict(), nullable=True)
    api_design: Mapped[Any | None] = mapped_column(JsonDict(), nullable=True)
    database_design: Mapped[Any | None] = mapped_column(JsonDict(), nullable=True)
    shared_components: Mapped[Any | None] = mapped_column(JsonDict(), nullable=True)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    
    # Artifact specific columns
    user_story_id: Mapped[str | None] = mapped_column(String(50), nullable=True)
    epic_id: Mapped[str | None] = mapped_column(String(50), nullable=True)
    file_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    file_path: Mapped[str | None] = mapped_column(Text, nullable=True)
    artifact_type: Mapped[str | None] = mapped_column(String(50), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    # ── Backward Compatibility Properties ─────────────────────────────
    @property
    def id(self) -> uuid.UUID:
        # pyrefly: ignore [bad-return]
        return self.blueprint_id

    @id.setter
    def id(self, value: uuid.UUID) -> None:
        self.blueprint_id = value

    @property
    def api_blueprint(self) -> Any | None:
        return self.api_design

    @api_blueprint.setter
    def api_blueprint(self, value: Any | None) -> None:
        self.api_design = value

    @property
    def workflow_blueprint(self) -> Any | None:
        return getattr(self, "_workflow_blueprint", None)

    @workflow_blueprint.setter
    def workflow_blueprint(self, value: Any | None) -> None:
        self._workflow_blueprint = value

    # ── Relationships ───────────────────────────────────────────────────
    project: Mapped["Project"] = relationship(  # noqa: F821
        "Project", back_populates="blueprints",
    )
    epics: Mapped[list["Epic"]] = relationship(  # noqa: F821
        "Epic", back_populates="blueprint", cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Blueprint blueprint_id={self.blueprint_id!s} project_id={self.project_id!s} v{self.version}>"

