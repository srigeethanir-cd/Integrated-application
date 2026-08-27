from __future__ import annotations

import hashlib
import json
import logging
import os
import time
from datetime import datetime, timezone
from typing import Any, Dict, Optional, Set
import urllib.parse
import urllib.request

from fastapi import WebSocket
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.connection import async_session_maker
from app.database.models import AppSetting

logger = logging.getLogger(__name__)

DEFAULT_PERSONALIZATION: Dict[str, Any] = {
    "logo_url": None,
    "theme": "purple-light",
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
    """Handles Cloudinary logo uploads, database persistence, and theme updates."""

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
        """Uploads image bytes to Cloudinary using secure signed API and returns the secure URL."""
        cloud_name, api_key, api_secret = self._get_cloudinary_config()
        timestamp = int(time.time())

        # Generate Cloudinary signature: params sorted alphabetically + api_secret hashed with SHA1
        # For a basic upload with timestamp and folder:
        folder = "storyforge_branding"
        to_sign = f"folder={folder}&timestamp={timestamp}{api_secret}"
        signature = hashlib.sha1(to_sign.encode("utf-8")).hexdigest()

        upload_url = f"https://api.cloudinary.com/v1_1/{cloud_name}/image/upload"

        # Build multipart/form-data request
        boundary = f"----WebKitFormBoundary{uuid_hex()[:16]}"
        lines = []

        def add_field(name: str, value: str):
            lines.append(f"--{boundary}".encode("utf-8"))
            lines.append(f'Content-Disposition: form-data; name="{name}"'.encode("utf-8"))
            lines.append(b"")
            lines.append(str(value).encode("utf-8"))

        add_field("api_key", api_key)
        add_field("timestamp", str(timestamp))
        add_field("folder", folder)
        add_field("signature", signature)

        # File field
        lines.append(f"--{boundary}".encode("utf-8"))
        lines.append(f'Content-Disposition: form-data; name="file"; filename="{filename}"'.encode("utf-8"))
        lines.append(b"Content-Type: image/png")
        lines.append(b"")
        lines.append(file_bytes)
        lines.append(f"--{boundary}--".encode("utf-8"))
        lines.append(b"")

        body = b"\r\n".join(lines)

        req = urllib.request.Request(
            upload_url,
            data=body,
            headers={
                "Content-Type": f"multipart/form-data; boundary={boundary}",
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
            raise ValueError(f"Cloudinary upload failed ({exc.code}): {err_body}") from exc
        except Exception as exc:
            logger.error("Cloudinary upload request failed: %s", exc)
            raise ValueError(f"Cloudinary connection error: {exc}") from exc

    async def get_personalization(self) -> Dict[str, Any]:
        """Fetches personalization settings from PostgreSQL database with fallback to memory."""
        try:
            async with async_session_maker() as session:
                stmt = select(AppSetting).where(AppSetting.key == "personalization")
                res = await session.execute(stmt)
                setting = res.scalar_one_or_none()
                if setting is not None and isinstance(setting.value, dict):
                    self._memory_cache.update(setting.value)
                    return dict(self._memory_cache)
        except Exception as exc:
            logger.warning("Database read for personalization failed, using cache: %s", exc)

        return dict(self._memory_cache)

    async def update_personalization(
        self,
        *,
        logo_url: Optional[str] = None,
        theme: Optional[str] = None,
        updated_by: str = "administrator",
    ) -> Dict[str, Any]:
        """Persists personalization settings to PostgreSQL and broadcasts update via WebSocket."""
        current = await self.get_personalization()

        if logo_url is not None or "logo_url" in current:
            current["logo_url"] = logo_url if logo_url != "" else None
        if theme is not None:
            current["theme"] = theme

        current["updated_at"] = datetime.now(timezone.utc).isoformat()
        current["updated_by"] = updated_by

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


def uuid_hex() -> str:
    import uuid
    return uuid.uuid4().hex


personalization_service = PersonalizationService()
