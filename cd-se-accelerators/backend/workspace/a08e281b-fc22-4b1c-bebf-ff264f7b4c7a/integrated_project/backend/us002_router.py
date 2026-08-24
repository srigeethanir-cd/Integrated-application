"""FastAPI Router for US002: User Login."""

from typing import Any, Dict, Optional
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

router = APIRouter(prefix="/user_login", tags=["UserLogin"])

class UserLoginRequest(BaseModel):
    username: str = Field(..., example="john_doe")
    password: str = Field(..., example="SecurePassword123!")


@router.post("/login", status_code=status.HTTP_200_OK)
def authenticate_user_session(payload: UserLoginRequest) -> Dict[str, Any]:
    """Authenticate user credentials and issue session JWT token for US002."""
    return {
        "status": "success",
        "story_key": "US002",
        "access_token": "jwt_tok_" + payload.username.lower() + "_auth",
        "token_type": "bearer",
        "expires_in_seconds": 3600
    }
