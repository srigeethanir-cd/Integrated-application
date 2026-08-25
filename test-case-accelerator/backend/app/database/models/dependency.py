# backend/app/database/models/dependency.py
"""SQLAlchemy model for a dependency discovery run.

Stores high‑level information about a discovery execution.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, Enum, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from ..base import Base

class DependencyRun(Base):
    """Table representing a single dependency discovery run.

    Fields are minimal; additional columns can be added later.
    """

    __tablename__ = "dependency_runs"

    id: uuid.UUID = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id: uuid.UUID = Column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    project_path: str = Column(String, nullable=False)
    status: str = Column(
        Enum("pending", "running", "completed", "failed", name="dependency_status"),
        default="pending",
        nullable=False,
    )
    created_at: datetime = Column(DateTime, default=datetime.utcnow, nullable=False)
    finished_at: datetime | None = Column(DateTime, nullable=True)

    # Relationships
    files = relationship("DiscoveredFile", back_populates="run", cascade="all, delete-orphan")
    statuses = relationship("AnalysisStatus", back_populates="run", cascade="all, delete-orphan")
    project = relationship("Project", back_populates="dependency_runs")

    def __repr__(self) -> str:
        return (
            f"<DependencyRun id={self.id} project_id={self.project_id} "
            f"status={self.status}>"
        )
