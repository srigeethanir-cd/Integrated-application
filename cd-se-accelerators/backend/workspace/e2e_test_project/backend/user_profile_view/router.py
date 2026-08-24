"""FastAPI Router for US-003: User Profile View."""

from typing import Any, Dict
from fastapi import APIRouter, HTTPException, status

router = APIRouter(prefix="/user_profile_view", tags=["UserProfileView"])


@router.post("/", status_code=status.HTTP_200_OK)
def handle_user_profile_view_action(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Execute API endpoint for User Profile View."""
    return {
        "status": "success",
        "story_key": "US-003",
        "action": "user_profile_view",
        "received": payload,
    }
