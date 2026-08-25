# backend/app/database/models/analysis_status.py
"""SQLAlchemy model representing the status of a discovery analysis.

Tracks stage-by-stage progress, retry count, and timestamps for the resume/retry pipeline.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, Enum, String, ForeignKey, Integer, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from ..base import Base

class AnalysisStatus(Base):
    """Table storing the status of a discovery run at a granular level.

    Tracks completion state, retry count, and timestamps.
    """

    __tablename__ = "analysis_status"

    id: uuid.UUID = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    run_id: uuid.UUID = Column(UUID(as_uuid=True), ForeignKey('dependency_runs.id', ondelete="CASCADE"), nullable=False)
    stage_number: int | None = Column(Integer, nullable=True)
    step: str = Column(String, nullable=False)
    status: str = Column(
        Enum("pending", "running", "completed", "failed", name="step_status"),
        default="pending",
        nullable=False,
    )
    retry_count: int = Column(Integer, default=0, nullable=False)
    started_at: datetime | None = Column(DateTime, nullable=True)
    completed_at: datetime | None = Column(DateTime, nullable=True)
    error_message: str | None = Column(Text, nullable=True)
    created_at: datetime = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: datetime = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationship back to DependencyRun
    run = relationship('DependencyRun', back_populates='statuses')

    def __repr__(self) -> str:
        return f"<AnalysisStatus run_id={self.run_id} step={self.step} status={self.status} stage={self.stage_number} retry={self.retry_count}>"
