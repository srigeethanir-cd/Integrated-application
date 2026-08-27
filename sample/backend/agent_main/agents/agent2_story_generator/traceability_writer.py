"""Traceability Writer — Records requirement-to-code traceability."""

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session

# pyrefly: ignore [missing-import]
from app.repository.generation_history_repository import GenerationHistoryRepository
# pyrefly: ignore [missing-import]
from app.repository.file_repository import FileRepository

logger = logging.getLogger(__name__)


class TraceabilityWriter:
    """Logs generation audit records into database tables."""

    def __init__(self, db: Optional[Session] = None) -> None:
        self.db = db

    def record_traceability(
        self,
        story_id: Any,
        action: str,
        status: str,
        files_affected: Optional[List[str]] = None,
        db_session: Optional[Session] = None,
    ) -> bool:
        """Record audit event in generation history repository."""
        session = db_session or self.db
        if not session:
            logger.info("Traceability record (in-memory): Story %s -> Action: %s, Status: %s, Files: %s", story_id, action, status, files_affected)
            return True

        try:
            gen_repo = GenerationHistoryRepository(session)
            gen_repo.create(
                story_id=story_id,
                agent="agent2_story_generator",
                action=action,
                status=status,
                execution_time=0.0,
            )
            logger.info("Recorded database traceability for story %s", story_id)
            return True
        except Exception as e:
            logger.warning("Failed to record database traceability: %s", str(e))
            return False
