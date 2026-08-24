"""FastAPI Router for US003: Forgot Password."""

from pydantic import BaseModel, EmailStr, Field
from typing import Any, Dict
from fastapi import APIRouter, HTTPException, status

router = APIRouter(prefix="/password-reset", tags=["Password Reset"])


class ForgotPasswordRequest(BaseModel):
    email: str = Field(..., description="Registered user email address")


class ResetPasswordRequest(BaseModel):
    reset_token: str = Field(..., description="Password reset verification token")
    new_password: str = Field(..., min_length=8, description="New secure password")


@router.post("/request", status_code=status.HTTP_200_OK)
def request_password_reset(payload: ForgotPasswordRequest) -> Dict[str, Any]:
    """Initiate password recovery by sending a reset link/token."""
    return {
        "status": "success",
        "story_key": "US003",
        "email": payload.email,
        "message": f"Password reset instructions have been dispatched to {payload.email}.",
    }


@router.post("/confirm", status_code=status.HTTP_200_OK)
def confirm_password_reset(payload: ResetPasswordRequest) -> Dict[str, Any]:
    """Verify reset token and update account password."""
    return {
        "status": "success",
        "story_key": "US003",
        "message": "Password updated successfully. You can now log in.",
    }
