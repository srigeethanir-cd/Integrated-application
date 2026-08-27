"""Context Builder Bridge — Bridges Agent-2 with Knowledge Service context builder."""

import logging
import uuid
from typing import Any, Dict, Optional, Union

logger = logging.getLogger(__name__)


class Agent2ContextBuilder:
    """Agent-2 wrapper for Knowledge Service ContextBuilder."""

    def __init__(self, db_session: Optional[Any] = None) -> None:
        self._db_session = db_session
        self._ks_context_builder = None

    def _get_ks_builder(self) -> Any:
        """Lazy-load the Knowledge Service ContextBuilder to avoid import-time DB errors."""
        if self._ks_context_builder is None:
            try:
                # pyrefly: ignore [missing-import]
                from app.services.knowledge_service.context_builder import ContextBuilder as KnowledgeContextBuilder
                self._ks_context_builder = KnowledgeContextBuilder(db=self._db_session)
            except Exception as e:
                logger.warning("Could not initialize KnowledgeContextBuilder: %s", str(e))
        return self._ks_context_builder

    def build_context(self, story_id: Union[str, uuid.UUID]) -> Dict[str, Any]:
        """Fetch strongly typed GenerationContext and convert to dictionary.

        Args:
            story_id: Target story ID or key.

        Returns:
            Dict containing generation context.
        """
        ks_builder = self._get_ks_builder()
        if ks_builder:
            try:
                ctx = ks_builder.build_generation_context(story_id)
                return ctx.model_dump()
            except Exception as e:
                logger.warning("Failed to fetch context from Knowledge Service: %s", str(e))

        return {
            "story": {"id": str(story_id), "story_key": str(story_id), "title": f"Story {story_id}"},
            "blueprint": None,
            "existing_components": [],
            "shared_components": {},
            "traceability": {},
        }

