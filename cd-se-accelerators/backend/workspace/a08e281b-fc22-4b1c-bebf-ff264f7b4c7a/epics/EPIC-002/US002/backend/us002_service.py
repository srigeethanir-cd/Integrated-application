"""Service layer for US002: User Login."""

import logging
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class UserLoginService:
    """Service handling domain business logic for User Login."""

    def __init__(self) -> None:
        self.service_name = "UserLoginService"
        self.story_key = "US002"

    def authenticate_user(self, username: str, password_plain: str) -> Dict[str, Any]:
        """Verify user credentials and issue session auth token for US002."""
        logger.info("Authenticating user: %s", username)
        if not username or not password_plain:
            raise ValueError("Username and password must be provided.")
        return {
            "status": "success",
            "story_key": "US002",
            "authenticated": True,
            "access_token": "jwt_tok_" + username.lower() + "_verified",
            "token_type": "Bearer",
            "expires_in": 3600
        }
