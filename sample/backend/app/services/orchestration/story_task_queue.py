"""Story Task Queue — In-memory task queue for story pipeline execution."""

import logging
from collections import deque
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class StoryTaskQueue:
    """Manages queue of user stories pending Agent-2 processing."""

    def __init__(self) -> None:
        self._queue: deque[Dict[str, Any]] = deque()
        self._completed: List[Dict[str, Any]] = []
        self._failed: List[Dict[str, Any]] = []

    def enqueue(self, story: Dict[str, Any]) -> None:
        """Add a story to pending queue."""
        self._queue.append(story)
        logger.info("Enqueued story: %s", story.get("story_key") or story.get("id"))

    def dequeue(self) -> Optional[Dict[str, Any]]:
        """Pop next story from queue."""
        if self._queue:
            return self._queue.popleft()
        return None

    def mark_completed(self, result: Dict[str, Any]) -> None:
        """Record completed story execution."""
        self._completed.append(result)

    def mark_failed(self, result: Dict[str, Any]) -> None:
        """Record failed story execution."""
        self._failed.append(result)

    def status(self) -> Dict[str, Any]:
        """Return queue summary status."""
        return {
            "pending_count": len(self._queue),
            "completed_count": len(self._completed),
            "failed_count": len(self._failed),
        }
