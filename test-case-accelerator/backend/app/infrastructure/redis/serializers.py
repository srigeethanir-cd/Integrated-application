"""JSON serialization helpers for cached values."""

from __future__ import annotations

import json
from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from pathlib import Path
from typing import Any
from uuid import UUID

from app.infrastructure.redis.exceptions import RedisSerializationError


class JsonSerializer:
    """Serialize common Python values to UTF-8 JSON and back."""

    @staticmethod
    def dumps(value: Any) -> bytes:
        """Serialize a JSON-compatible value.

        Args:
            value: Value to encode.

        Returns:
            UTF-8 encoded JSON bytes.

        Raises:
            RedisSerializationError: If the value cannot be encoded.
        """
        try:
            return json.dumps(value, default=JsonSerializer._default).encode("utf-8")
        except (TypeError, ValueError) as error:
            raise RedisSerializationError("Cache value is not JSON serializable.") from error

    @staticmethod
    def loads(value: bytes | str) -> Any:
        """Deserialize a JSON value.

        Args:
            value: UTF-8 JSON bytes or text.

        Returns:
            The decoded Python value.

        Raises:
            RedisSerializationError: If the payload is invalid JSON.
        """
        try:
            return json.loads(value)
        except (TypeError, UnicodeDecodeError, json.JSONDecodeError) as error:
            raise RedisSerializationError("Cached value contains invalid JSON.") from error

    @staticmethod
    def _default(value: Any) -> str:
        """Convert supported non-JSON scalar values to strings.

        Args:
            value: Scalar requested by the JSON encoder.

        Returns:
            A stable string representation.

        Raises:
            TypeError: If the value has no supported representation.
        """
        if isinstance(value, (datetime, date)):
            return value.isoformat()
        if isinstance(value, (UUID, Decimal, Path, Enum)):
            return str(value.value if isinstance(value, Enum) else value)
        raise TypeError(f"Unsupported cache value type: {type(value).__name__}")
