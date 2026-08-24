"""FastAPI Router for US010: Logout."""

from typing import Any, Dict
from fastapi import APIRouter, HTTPException, status

router = APIRouter(prefix="/feature", tags=["Feature"])


@router.post("/", status_code=status.HTTP_200_OK)
def handle_feature_action(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Execute API endpoint for Logout."""
    return {
        "status": "success",
        "story_key": "US010",
        "action": "feature",
        "received": payload,
    }
