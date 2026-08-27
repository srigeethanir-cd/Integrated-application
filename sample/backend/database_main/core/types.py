"""Cross-database column type helpers.

Provides ``GUID`` and ``JsonDict`` types that use native PostgreSQL
``UUID`` / ``JSONB`` when available and fall back to portable
alternatives (``CHAR(32)`` / ``JSON``) for SQLite during testing.
"""

import uuid

from sqlalchemy import JSON, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.types import CHAR, TypeDecorator


class GUID(TypeDecorator):
    """Platform-independent UUID type.

    Uses PostgreSQL's native ``UUID`` type when available, otherwise
    falls back to ``CHAR(32)`` and stores the hex string.
    """

    impl = CHAR
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(UUID(as_uuid=True))
        return dialect.type_descriptor(CHAR(32))

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        if isinstance(value, uuid.UUID):
            u_val = value
        else:
            try:
                u_val = uuid.UUID(value)
            except ValueError:
                u_val = uuid.uuid5(uuid.NAMESPACE_DNS, str(value))
        if dialect.name == "postgresql":
            return u_val
        return u_val.hex

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        if isinstance(value, uuid.UUID):
            return value
        try:
            return uuid.UUID(value)
        except ValueError:
            return uuid.uuid5(uuid.NAMESPACE_DNS, str(value))


class JsonDict(TypeDecorator):
    """Platform-independent JSON type.

    Uses PostgreSQL's ``JSONB`` when available, otherwise standard ``JSON``.
    """

    impl = JSON
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(JSONB())
        return dialect.type_descriptor(JSON())
