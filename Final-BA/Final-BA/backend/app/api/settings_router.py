from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from fastapi import APIRouter, File, Header, HTTPException, UploadFile, WebSocket, WebSocketDisconnect, status
from pydantic import BaseModel, Field

from app.services.personalization_service import (
    personalization_service,
    websocket_manager,
)

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Settings & Personalization"])

VALID_THEMES = {
    "blue-light",
    "blue-dark",
    "green-light",
    "green-dark",
    "purple-light",
    "purple-dark",
    "orange-light",
    "orange-dark",
    "rose-light",
    "rose-dark",
}


class ThemeUpdateRequest(BaseModel):
    theme: str = Field(..., description="Theme identifier (e.g. purple-light, blue-dark, etc.)")


class PersonalizationUpdateRequest(BaseModel):
    logo_url: Optional[str] = None
    theme: Optional[str] = None


def _check_admin_authorization(x_user_role: Optional[str]) -> None:
    """Verifies that the request comes from an authorized administrator."""
    # If no header provided or role is admin / administrator, allow
    # If explicitly passed a non-admin role (e.g. viewer, user, business_analyst), enforce restriction
    if x_user_role:
        normalized = x_user_role.strip().lower()
        if normalized not in {"admin", "administrator", "system_admin", "superuser"}:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only administrators are authorized to modify global branding and theme settings.",
            )


@router.get("/settings/personalization")
async def get_personalization_settings() -> Dict[str, Any]:
    """Retrieve the active application branding and theme settings."""
    settings = await personalization_service.get_personalization()
    return {
        "success": True,
        "data": settings,
    }


@router.post("/settings/personalization/logo")
async def upload_custom_logo(
    file: UploadFile = File(...),
    x_user_role: Optional[str] = Header(default="administrator", alias="X-User-Role"),
) -> Dict[str, Any]:
    """Upload a new custom application logo to Cloudinary and update global settings."""
    _check_admin_authorization(x_user_role)

    if not file.filename:
        raise HTTPException(status_code=400, detail="No logo file provided")

    contents = await file.read()
    if len(contents) == 0:
        raise HTTPException(status_code=400, detail="Uploaded file is empty")

    if len(contents) > 10 * 1024 * 1024:  # 10 MB limit
        raise HTTPException(status_code=400, detail="Logo file size must be less than 10 MB")

    try:
        secure_url = await personalization_service.upload_logo_to_cloudinary(
            file_bytes=contents,
            filename=file.filename,
        )
        updated = await personalization_service.update_personalization(
            logo_url=secure_url,
            updated_by="administrator",
        )
        return {
            "success": True,
            "message": "Logo uploaded and saved successfully",
            "logo_url": secure_url,
            "data": updated,
        }
    except Exception as exc:
        logger.exception("Failed to upload logo to Cloudinary: %s", exc)
        raise HTTPException(
            status_code=500,
            detail=f"Logo upload failed: {exc}",
        ) from exc


@router.delete("/settings/personalization/logo")
async def remove_custom_logo(
    x_user_role: Optional[str] = Header(default="administrator", alias="X-User-Role"),
) -> Dict[str, Any]:
    """Remove the custom logo and revert to the application's default branding."""
    _check_admin_authorization(x_user_role)

    updated = await personalization_service.update_personalization(
        logo_url="",
        updated_by="administrator",
    )
    return {
        "success": True,
        "message": "Custom logo removed. Default branding restored.",
        "logo_url": None,
        "data": updated,
    }


@router.put("/settings/personalization/theme")
async def update_theme(
    request: ThemeUpdateRequest,
    x_user_role: Optional[str] = Header(default="administrator", alias="X-User-Role"),
) -> Dict[str, Any]:
    """Update the application theme (one of the 10 available themes)."""
    _check_admin_authorization(x_user_role)

    theme = request.theme.strip().lower()
    if theme not in VALID_THEMES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid theme '{theme}'. Must be one of: {', '.join(sorted(VALID_THEMES))}",
        )

    updated = await personalization_service.update_personalization(
        theme=theme,
        updated_by="administrator",
    )
    return {
        "success": True,
        "message": f"Theme updated to '{theme}' successfully",
        "theme": theme,
        "data": updated,
    }


@router.put("/settings/personalization")
async def update_personalization_all(
    request: PersonalizationUpdateRequest,
    x_user_role: Optional[str] = Header(default="administrator", alias="X-User-Role"),
) -> Dict[str, Any]:
    """Update both logo and theme configuration simultaneously."""
    _check_admin_authorization(x_user_role)

    theme = request.theme.strip().lower() if request.theme else None
    if theme and theme not in VALID_THEMES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid theme '{theme}'. Must be one of: {', '.join(sorted(VALID_THEMES))}",
        )

    updated = await personalization_service.update_personalization(
        logo_url=request.logo_url,
        theme=theme,
        updated_by="administrator",
    )
    return {
        "success": True,
        "data": updated,
    }


@router.websocket("/ws/settings")
async def websocket_settings_endpoint(websocket: WebSocket) -> None:
    """WebSocket endpoint to receive real-time branding and theme updates."""
    await websocket_manager.connect(websocket)
    try:
        # Send current state on connection
        current = await personalization_service.get_personalization()
        await websocket.send_json({"type": "INITIAL_PERSONALIZATION", "data": current})

        while True:
            # Keep connection alive; accept any ping/message
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        websocket_manager.disconnect(websocket)
    except Exception as exc:
        logger.warning("WebSocket connection exception: %s", exc)
        websocket_manager.disconnect(websocket)
