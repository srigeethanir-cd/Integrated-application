from __future__ import annotations

import base64
import hashlib
import json
import logging
import mimetypes
import os
import time
from datetime import datetime, timezone
from typing import Any, Dict, Optional, Set
import urllib.parse
import urllib.request

from fastapi import WebSocket
from sqlalchemy import select

from app.database.connection import async_session_maker
from app.database.models import AppSetting

logger = logging.getLogger(__name__)

DEFAULT_PERSONALIZATION: Dict[str, Any] = {
    "logo_url": None,
    "logo_shape": "rounded",
    "sidebar_bg": "#1B1B3A",
    "highlight_from": "#FF5722",
    "highlight_via": "#7B3FE4",
    "updated_at": datetime.now(timezone.utc).isoformat(),
    "updated_by": "system",
}


class PersonalizationWebSocketManager:
    """Manages active WebSocket connections to broadcast real-time personalization updates."""

    def __init__(self) -> None:
        self._active_connections: Set[WebSocket] = set()

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        self._active_connections.add(websocket)
        logger.info("Personalization WebSocket client connected (total: %d)", len(self._active_connections))

    def disconnect(self, websocket: WebSocket) -> None:
        self._active_connections.discard(websocket)
        logger.info("Personalization WebSocket client disconnected (remaining: %d)", len(self._active_connections))

    async def broadcast(self, event_type: str, payload: Dict[str, Any]) -> None:
        if not self._active_connections:
            return

        message = json.dumps({"type": event_type, "data": payload})
        dead_connections: Set[WebSocket] = set()

        for connection in list(self._active_connections):
            try:
                await connection.send_text(message)
            except Exception as exc:
                logger.warning("Failed to send WebSocket message: %s", exc)
                dead_connections.add(connection)

        for dead in dead_connections:
            self._active_connections.discard(dead)


websocket_manager = PersonalizationWebSocketManager()


class PersonalizationService:
    """Handles Cloudinary logo uploads, database persistence, logo shape, and sidebar color updates."""

    def __init__(self) -> None:
        self._memory_cache: Dict[str, Any] = dict(DEFAULT_PERSONALIZATION)

    def _get_cloudinary_config(self) -> tuple[str, str, str]:
        cloud_name = os.getenv("CLOUDINARY_CLOUD_NAME", "q5kbjmch").strip()
        api_key = os.getenv("CLOUDINARY_API_KEY", "886515727216551").strip()
        api_secret = os.getenv("CLOUDINARY_API_SECRET", "wBkg0HWuPgpUiF-rMJWRsOgXsaQ").strip()

        if not cloud_name or not api_key or not api_secret:
            raise ValueError("Cloudinary credentials are not configured on the server")

        return cloud_name, api_key, api_secret

    async def upload_logo_to_cloudinary(self, file_bytes: bytes, filename: str) -> str:
        """Uploads image bytes to Cloudinary using base64 data URI and returns the secure URL."""
        cloud_name, api_key, api_secret = self._get_cloudinary_config()
        timestamp = int(time.time())
        folder = "storyforge_branding"

        # Determine MIME type
        mime_type, _ = mimetypes.guess_type(filename)
        if not mime_type or not mime_type.startswith("image/"):
            ext = os.path.splitext(filename)[1].lower()
            if ext == ".png":
                mime_type = "image/png"
            elif ext in [".jpg", ".jpeg"]:
                mime_type = "image/jpeg"
            elif ext == ".svg":
                mime_type = "image/svg+xml"
            elif ext == ".webp":
                mime_type = "image/webp"
            else:
                mime_type = "image/png"

        b64_encoded = base64.b64encode(file_bytes).decode("ascii")
        data_uri = f"data:{mime_type};base64,{b64_encoded}"

        # Generate signed parameters
        to_sign = f"folder={folder}&timestamp={timestamp}{api_secret}"
        signature = hashlib.sha1(to_sign.encode("utf-8")).hexdigest()

        upload_url = f"https://api.cloudinary.com/v1_1/{cloud_name}/image/upload"

        post_data = urllib.parse.urlencode({
            "file": data_uri,
            "api_key": api_key,
            "timestamp": str(timestamp),
            "folder": folder,
            "signature": signature,
        }).encode("utf-8")

        req = urllib.request.Request(
            upload_url,
            data=post_data,
            headers={
                "Content-Type": "application/x-www-form-urlencoded",
                "User-Agent": "StoryForge-AI/1.0",
            },
            method="POST",
        )

        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                resp_data = json.loads(resp.read().decode("utf-8"))
                secure_url = resp_data.get("secure_url") or resp_data.get("url")
                if not secure_url:
                    raise ValueError(f"Cloudinary upload succeeded but no URL returned: {resp_data}")
                logger.info("Successfully uploaded logo to Cloudinary: %s", secure_url)
                return str(secure_url)
        except urllib.error.HTTPError as exc:
            err_body = exc.read().decode("utf-8", errors="replace")
            logger.error("Cloudinary HTTP Error %s: %s", exc.code, err_body)
            # If Cloudinary fails (e.g. rate-limit or network issue), fallback gracefully to data URI
            logger.warning("Falling back to local Data URI representation for uploaded logo")
            return data_uri
        except Exception as exc:
            logger.error("Cloudinary upload request failed: %s", exc)
            logger.warning("Falling back to local Data URI representation for uploaded logo")
            return data_uri

    async def get_personalization(self) -> Dict[str, Any]:
        """Fetches personalization settings from PostgreSQL database with fallback to memory."""
        try:
            async with async_session_maker() as session:
                stmt = select(AppSetting).where(AppSetting.key == "personalization")
                res = await session.execute(stmt)
                setting = res.scalar_one_or_none()
                if setting is not None and isinstance(setting.value, dict):
                    self._memory_cache.update(setting.value)
                    for key, default_val in DEFAULT_PERSONALIZATION.items():
                        if key not in self._memory_cache or self._memory_cache[key] is None and key != "logo_url":
                            self._memory_cache[key] = default_val
                    return dict(self._memory_cache)
        except Exception as exc:
            logger.warning("Database read for personalization failed, using cache: %s", exc)

        return dict(self._memory_cache)

    async def update_personalization(
        self,
        *,
        logo_url: Optional[str] = None,
        logo_shape: Optional[str] = None,
        sidebar_bg: Optional[str] = None,
        highlight_from: Optional[str] = None,
        highlight_via: Optional[str] = None,
        updated_by: str = "administrator",
    ) -> Dict[str, Any]:
        """Persists personalization settings to PostgreSQL and broadcasts update via WebSocket."""
        current = await self.get_personalization()

        if logo_url is not None:
            current["logo_url"] = logo_url if logo_url != "" else None
        if logo_shape is not None:
            current["logo_shape"] = logo_shape.strip().lower()
        if sidebar_bg is not None:
            current["sidebar_bg"] = sidebar_bg
        if highlight_from is not None:
            current["highlight_from"] = highlight_from
        if highlight_via is not None:
            current["highlight_via"] = highlight_via

        current["updated_at"] = datetime.now(timezone.utc).isoformat()
        current["updated_by"] = updated_by

        current.pop("theme", None)

        self._memory_cache.update(current)

        # Save to database
        try:
            async with async_session_maker() as session:
                stmt = select(AppSetting).where(AppSetting.key == "personalization")
                res = await session.execute(stmt)
                setting = res.scalar_one_or_none()

                if setting is None:
                    setting = AppSetting(key="personalization", value=current)
                    session.add(setting)
                else:
                    setting.value = current
                    setting.updated_at = datetime.now(timezone.utc)

                await session.commit()
                logger.info("Persisted personalization settings to database: %s", current)
        except Exception as exc:
            logger.error("Failed to persist personalization settings to database: %s", exc)

        # Broadcast update in real-time to all connected WebSocket clients
        await websocket_manager.broadcast("PERSONALIZATION_UPDATED", current)

        return dict(current)

    async def reset_personalization(self, updated_by: str = "administrator") -> Dict[str, Any]:
        """Resets personalization settings to application defaults and broadcasts."""
        defaults = dict(DEFAULT_PERSONALIZATION)
        defaults["updated_at"] = datetime.now(timezone.utc).isoformat()
        defaults["updated_by"] = updated_by

        self._memory_cache = dict(defaults)

        try:
            async with async_session_maker() as session:
                stmt = select(AppSetting).where(AppSetting.key == "personalization")
                res = await session.execute(stmt)
                setting = res.scalar_one_or_none()

                if setting is None:
                    setting = AppSetting(key="personalization", value=defaults)
                    session.add(setting)
                else:
                    setting.value = defaults
                    setting.updated_at = datetime.now(timezone.utc)

                await session.commit()
                logger.info("Reset personalization settings in database: %s", defaults)
        except Exception as exc:
            logger.error("Failed to reset personalization settings in database: %s", exc)

        await websocket_manager.broadcast("PERSONALIZATION_UPDATED", defaults)
        return dict(defaults)


def uuid_hex() -> str:
    import uuid
    return uuid.uuid4().hex


personalization_service = PersonalizationService()
