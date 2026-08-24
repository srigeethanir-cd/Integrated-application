"""FastAPI Router for US-002: User Login."""

from typing import Any, Dict
from fastapi import APIRouter, HTTPException, status

router = APIRouter(prefix="/user_login", tags=["UserLogin"])


@router.post("/", status_code=status.HTTP_200_OK)
def handle_user_login_action(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Execute API endpoint for User Login."""
    return {
        "status": "success",
        "story_key": "US-002",
        "action": "user_login",
        "received": payload,
    }
