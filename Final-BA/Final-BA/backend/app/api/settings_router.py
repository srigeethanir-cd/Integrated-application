from __future__ import annotations

import logging
import re
from typing import Any, Dict, Optional

from fastapi import APIRouter, File, Header, HTTPException, UploadFile, WebSocket, WebSocketDisconnect, status
from pydantic import BaseModel, Field

from app.services.personalization_service import (
    personalization_service,
    websocket_manager,
)

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Settings & Personalization"])

HEX_COLOR_RE = re.compile(r"^#[0-9a-fA-F]{6}$")
VALID_LOGO_SHAPES = {"square", "rounded", "circle"}


class SidebarColorsRequest(BaseModel):
    sidebar_bg: str = Field(..., description="Sidebar background hex color, e.g. #1B1B3A")
    highlight_from: str = Field(..., description="Highlight gradient from-color hex, e.g. #FF5722")
    highlight_via: str = Field(..., description="Highlight gradient via-color hex, e.g. #7B3FE4")


class PersonalizationUpdateRequest(BaseModel):
    logo_url: Optional[str] = None
    logo_shape: Optional[str] = None
    sidebar_bg: Optional[str] = None
    highlight_from: Optional[str] = None
    highlight_via: Optional[str] = None


def _check_admin_authorization(x_user_role: Optional[str]) -> None:
    """Verifies that the request comes from an authorized administrator."""
    if x_user_role:
        normalized = x_user_role.strip().lower()
        if normalized not in {"admin", "administrator", "system_admin", "superuser"}:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only administrators are authorized to modify personalization settings.",
            )


def _validate_hex_color(value: str, field_name: str) -> str:
    """Validate and normalize a hex color string."""
    value = value.strip()
    if not HEX_COLOR_RE.match(value):
        raise HTTPException(
            status_code=400,
            detail=f"Invalid hex color for '{field_name}': '{value}'. Expected format: #RRGGBB",
        )
    return value


def _validate_logo_shape(value: str) -> str:
    """Validate logo shape string."""
    value = value.strip().lower()
    if value not in VALID_LOGO_SHAPES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid logo shape '{value}'. Must be one of: {', '.join(sorted(VALID_LOGO_SHAPES))}",
        )
    return value


@router.get("/settings/personalization")
async def get_personalization_settings() -> Dict[str, Any]:
    """Retrieve the active application branding and sidebar personalization settings."""
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


@router.put("/settings/personalization/sidebar")
async def update_sidebar_colors(
    request: SidebarColorsRequest,
    x_user_role: Optional[str] = Header(default="administrator", alias="X-User-Role"),
) -> Dict[str, Any]:
    """Update sidebar background and highlight gradient colors."""
    _check_admin_authorization(x_user_role)

    sidebar_bg = _validate_hex_color(request.sidebar_bg, "sidebar_bg")
    highlight_from = _validate_hex_color(request.highlight_from, "highlight_from")
    highlight_via = _validate_hex_color(request.highlight_via, "highlight_via")

    updated = await personalization_service.update_personalization(
        sidebar_bg=sidebar_bg,
        highlight_from=highlight_from,
        highlight_via=highlight_via,
        updated_by="administrator",
    )
    return {
        "success": True,
        "message": "Sidebar colors updated successfully",
        "data": updated,
    }


@router.put("/settings/personalization")
async def update_personalization_all(
    request: PersonalizationUpdateRequest,
    x_user_role: Optional[str] = Header(default="administrator", alias="X-User-Role"),
) -> Dict[str, Any]:
    """Update personalization settings (logo, shape, and sidebar colors)."""
    _check_admin_authorization(x_user_role)

    logo_shape = _validate_logo_shape(request.logo_shape) if request.logo_shape else None
    sidebar_bg = _validate_hex_color(request.sidebar_bg, "sidebar_bg") if request.sidebar_bg else None
    highlight_from = _validate_hex_color(request.highlight_from, "highlight_from") if request.highlight_from else None
    highlight_via = _validate_hex_color(request.highlight_via, "highlight_via") if request.highlight_via else None

    updated = await personalization_service.update_personalization(
        logo_url=request.logo_url,
        logo_shape=logo_shape,
        sidebar_bg=sidebar_bg,
        highlight_from=highlight_from,
        highlight_via=highlight_via,
        updated_by="administrator",
    )
    return {
        "success": True,
        "message": "Personalization settings saved successfully",
        "data": updated,
    }


@router.post("/settings/personalization/reset")
async def reset_personalization_endpoint(
    x_user_role: Optional[str] = Header(default="administrator", alias="X-User-Role"),
) -> Dict[str, Any]:
    """Reset all personalization settings to application defaults."""
    _check_admin_authorization(x_user_role)

    defaults = await personalization_service.reset_personalization(updated_by="administrator")
    return {
        "success": True,
        "message": "Personalization settings reset to application defaults",
        "data": defaults,
    }


@router.websocket("/ws/settings")
async def websocket_settings_endpoint(websocket: WebSocket) -> None:
    """WebSocket endpoint to receive real-time branding and sidebar color updates."""
    await websocket_manager.connect(websocket)
    try:
        current = await personalization_service.get_personalization()
        await websocket.send_json({"type": "INITIAL_PERSONALIZATION", "data": current})

        while True:
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        websocket_manager.disconnect(websocket)
    except Exception as exc:
        logger.warning("WebSocket connection exception: %s", exc)
        websocket_manager.disconnect(websocket)
