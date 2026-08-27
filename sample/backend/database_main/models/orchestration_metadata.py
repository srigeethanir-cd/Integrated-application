import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, JSON, Integer, DateTime, ForeignKey
from database_main.core.base import Base
from database_main.core.types import GUID

def generate_uuid():
    return str(uuid.uuid4())


class RollbackHistoryRecord(Base):
    __tablename__ = "rollback_history_records"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    project_id = Column(GUID(), ForeignKey("projects.project_id", ondelete="CASCADE"), nullable=False, index=True)
    story_key = Column(String(50), nullable=False)
    backup_checkpoint_name = Column(String(255), nullable=False)
    reason = Column(String(1000), nullable=True)
    rolled_back_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

