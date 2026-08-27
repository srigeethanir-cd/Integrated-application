"""Bounded retry helpers for transient database connectivity failures."""

from __future__ import annotations

from sqlalchemy.exc import IntegrityError, OperationalError, ProgrammingError


MAX_DATABASE_RETRIES = 3
DATABASE_RETRY_BASE_DELAY_SECONDS = 0.1

_TRANSIENT_MARKERS = (
    "connection reset",
    "connection refused",
    "connection timed out",
    "could not connect",
    "could not resolve",
    "dns",
    "name resolution",
    "network is unreachable",
    "server closed the connection",
    "temporary failure",
    "terminating connection",
    "timeout expired",
)


def is_transient_database_error(error: BaseException) -> bool:
    """Identify connectivity failures without retrying data/schema errors."""
    if isinstance(error, (IntegrityError, ProgrammingError)):
        return False
    if isinstance(error, OperationalError):
        return True
    if isinstance(error, (ConnectionError, OSError)):
        return any(marker in str(error).casefold() for marker in _TRANSIENT_MARKERS)
    return False


def retry_delay(attempt: int) -> float:
    """Return bounded exponential delay for a one-based retry attempt."""
    return min(
        DATABASE_RETRY_BASE_DELAY_SECONDS * (2 ** max(attempt - 1, 0)),
        1.0,
    )


__all__ = [
    "MAX_DATABASE_RETRIES",
    "is_transient_database_error",
    "retry_delay",
]
