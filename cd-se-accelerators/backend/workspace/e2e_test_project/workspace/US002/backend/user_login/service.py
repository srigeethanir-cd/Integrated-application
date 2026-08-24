"""Service layer for US-002: User Login."""

import logging
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class UserLoginService:
    """Service handling business logic for User Login."""

    def __init__(self) -> None:
        self.name = "UserLoginService"

    def execute(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Execute User Login business flow."""
        logger.info("Executing UserLoginService with payload: %s", payload)
        return {
            "status": "success",
            "story_key": "US-002",
            "message": "User Login executed successfully.",
            "data": payload,
        }
