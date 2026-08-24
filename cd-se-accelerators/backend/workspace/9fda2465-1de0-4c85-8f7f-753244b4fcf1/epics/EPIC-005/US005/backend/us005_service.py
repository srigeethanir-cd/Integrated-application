"""Service layer for US005: Logout."""

import logging
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class FeatureService:
    """Service handling business logic for Logout."""

    def __init__(self) -> None:
        self.name = "FeatureService"

    def execute(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Execute Logout business flow."""
        logger.info("Executing FeatureService with payload: %s", payload)
        return {
            "status": "success",
            "story_key": "US005",
            "message": "Logout executed successfully.",
            "data": payload,
        }
