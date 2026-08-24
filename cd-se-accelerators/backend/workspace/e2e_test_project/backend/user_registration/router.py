"""FastAPI Router for US-001: User Registration."""

from typing import Any, Dict
from fastapi import APIRouter, HTTPException, status

router = APIRouter(prefix="/user_registration", tags=["UserRegistration"])


@router.post("/", status_code=status.HTTP_200_OK)
def handle_user_registration_action(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Execute API endpoint for User Registration."""
    return {
        "status": "success",
        "story_key": "US-001",
        "action": "user_registration",
        "received": payload,
    }
