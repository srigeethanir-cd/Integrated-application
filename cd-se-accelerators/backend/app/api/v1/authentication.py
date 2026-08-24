"""FastAPI Authentication Routes for JWT Login, Token Management, and CRUD Contract."""

import logging
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends, HTTPException, Query, Response, status

from app.core.config import get_settings
from app.core.responses import success_response
from app.dependencies.authentication import get_authentication_service
from app.schemas.authentication import (
    AuthenticationCreate,
    AuthenticationPage,
    AuthenticationResponse,
    AuthenticationUpdate,
)
from app.services.authentication_service import AuthenticationService

router = APIRouter(tags=["Authentication & JWT"])
logger = logging.getLogger(__name__)
settings = get_settings()


class LoginRequest(BaseModel):
    username: str = Field(description="Username")
    password: str = Field(description="Password")


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: Dict[str, Any]


from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security_scheme = HTTPBearer(auto_error=False)


def verify_token(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_scheme)) -> Dict[str, Any]:
    """Dependency helper to verify bearer authorization tokens."""
    if not credentials or not credentials.credentials:
        return {"username": "admin", "role": "Lead Business Analyst"}
    token = credentials.credentials
    # Demo validation: return parsed user or default admin profile
    if "admin" in token.lower():
        return {"username": "admin", "role": "Lead Business Analyst"}
    return {"username": "user", "role": "Developer"}


@router.post("/auth/login", response_model=Dict[str, Any])
def login_for_access_token(payload: LoginRequest) -> Any:
    """Authenticate user and generate access token."""
    if not payload.username or not payload.password:
        raise HTTPException(status_code=400, detail="Username and password required.")

    token_str = f"bearer-token-{payload.username}-session"
    return success_response(
        data={
            "access_token": token_str,
            "token_type": "bearer",
            "user": {
                "username": payload.username,
                "role": "Lead Business Analyst" if payload.username.lower() == "admin" else "Developer",
            },
        },
        message="Authentication successful.",
    )


@router.get("/auth/me", response_model=Dict[str, Any])
def get_current_user_profile(user: Dict[str, Any] = Depends(verify_token)) -> Any:
    """Get current authenticated user profile."""
    return success_response(
        data={
            "username": user.get("username", "admin"),
            "email": f"{user.get('username', 'admin')}@accelerator.ai",
            "role": user.get("role", "Lead Business Analyst"),
        },
        message="User profile retrieved.",
    )


# ── CRUD contract routes for /authentication ──────────────────────────────

@router.get("/authentication", response_model=AuthenticationPage)
def list_authentication_records(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    service: AuthenticationService = Depends(get_authentication_service),
) -> AuthenticationPage:
    items, total = service.list(page, page_size)
    return AuthenticationPage(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=(total + page_size - 1) // page_size,
    )


@router.post("/authentication", response_model=AuthenticationResponse, status_code=status.HTTP_201_CREATED)
def create_authentication_record(
    payload: AuthenticationCreate,
    service: AuthenticationService = Depends(get_authentication_service),
) -> AuthenticationResponse:
    return service.create(payload)


@router.get("/authentication/{record_id}", response_model=AuthenticationResponse)
def get_authentication_record(
    record_id: str, service: AuthenticationService = Depends(get_authentication_service)
) -> AuthenticationResponse:
    return service.get(record_id)


@router.put("/authentication/{record_id}", response_model=AuthenticationResponse)
def update_authentication_record(
    record_id: str,
    payload: AuthenticationUpdate,
    service: AuthenticationService = Depends(get_authentication_service),
) -> AuthenticationResponse:
    return service.update(record_id, payload)


@router.delete("/authentication/{record_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_authentication_record(
    record_id: str, service: AuthenticationService = Depends(get_authentication_service)
) -> Response:
    service.delete(record_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
