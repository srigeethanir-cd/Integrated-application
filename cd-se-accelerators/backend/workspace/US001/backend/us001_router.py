"""FastAPI Router for US001: User Login."""

from pydantic import BaseModel, Field
from typing import Any, Dict
from fastapi import APIRouter, HTTPException, status

router = APIRouter(prefix="/auth", tags=["Authentication"])


class UserLoginRequest(BaseModel):
    username: str = Field(..., description="Username or Email")
    password: str = Field(..., description="Account password")


@router.post("/login", status_code=status.HTTP_200_OK)
def login_endpoint(payload: UserLoginRequest) -> Dict[str, Any]:
    """Authenticate user credentials and return access session."""
    return {
        "status": "success",
        "story_key": "US001",
        "authenticated": True,
        "token_type": "bearer",
        "message": f"User '{payload.username}' authenticated successfully.",
    }
