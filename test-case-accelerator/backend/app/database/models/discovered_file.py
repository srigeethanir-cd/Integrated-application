# backend/app/database/models/discovered_file.py
"""SQLAlchemy model representing metadata for a discovered source file.

Fields correspond to the ``FileMetadata`` schema defined in the schemas
package. Additional columns may be added in later stages.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, JSON, String, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from ..base import Base

class DiscoveredFile(Base):
    """Table storing per‑file discovery information.

    The ``metadata`` column holds a JSON representation of the ``FileMetadata``
    schema. ``is_entry_point`` is stored as a separate boolean for easy queries.
    """

    __tablename__ = "discovered_files"

    id: uuid.UUID = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    run_id: uuid.UUID = Column(UUID(as_uuid=True), ForeignKey('dependency_runs.id', ondelete="CASCADE"), nullable=False)
    path: str = Column(String(2048), nullable=False)
    language: String = Column(String, nullable=False)
    is_entry_point: bool = Column(Boolean, default=False, nullable=False)
    imports: JSON = Column(JSON, nullable=True)
    classes: JSON = Column(JSON, nullable=True)
    functions: JSON = Column(JSON, nullable=True)
    created_at: datetime = Column(DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self) -> str:
        return f"<DiscoveredFile id={self.id} path={self.path}>"

    # Relationship back to DependencyRun
    run = relationship('DependencyRun', back_populates='files')
