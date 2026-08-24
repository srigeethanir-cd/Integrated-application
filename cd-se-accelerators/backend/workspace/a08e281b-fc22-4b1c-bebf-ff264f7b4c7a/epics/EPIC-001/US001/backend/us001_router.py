"""FastAPI Router for US001: User Registration."""

from typing import Any, Dict, Optional
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

router = APIRouter(prefix="/user_registration", tags=["UserRegistration"])

class UserRegistrationRequest(BaseModel):
    name: str = Field(..., example="UserRegistration Item")
    payload: Dict[str, Any] = Field(default_factory=dict)


@router.post("/execute", status_code=status.HTTP_200_OK)
def handle_user_registration_action(request: UserRegistrationRequest) -> Dict[str, Any]:
    """Execute API endpoint for User Registration."""
    return {
        "status": "success",
        "story_key": "US001",
        "action": "user_registration",
        "data": request.model_dump() if hasattr(request, "model_dump") else request.dict()
    }
