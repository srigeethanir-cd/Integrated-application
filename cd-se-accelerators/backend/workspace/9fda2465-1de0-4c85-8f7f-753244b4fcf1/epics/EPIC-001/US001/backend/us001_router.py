"""FastAPI Router for US001: User Login."""

from typing import Any, Dict
from fastapi import APIRouter, HTTPException, status

router = APIRouter(prefix="/feature", tags=["Feature"])


@router.post("/", status_code=status.HTTP_200_OK)
def handle_feature_action(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Execute API endpoint for User Login."""
    return {
        "status": "success",
        "story_key": "US001",
        "action": "feature",
        "received": payload,
    }
