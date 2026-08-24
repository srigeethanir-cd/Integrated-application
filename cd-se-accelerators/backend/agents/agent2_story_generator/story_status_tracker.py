"""Story Status Tracker — Tracks story execution state."""

import logging
from datetime import datetime, timezone
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class StoryStatusTracker:
    """Tracks execution status of stories in memory and repository."""

    def __init__(self) -> None:
        self._statuses: Dict[str, Dict[str, Any]] = {}

    def update_status(self, story_id: str, status: str, details: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Update and record status for a story."""
        record = {
            "story_id": story_id,
            "status": status,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "details": details or {},
        }
        self._statuses[story_id] = record
        logger.info("Story %s status updated -> %s", story_id, status)
        return record

    def get_status(self, story_id: str) -> Optional[Dict[str, Any]]:
        """Get recorded status for a story."""
        return self._statuses.get(story_id)
