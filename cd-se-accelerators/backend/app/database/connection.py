"""PostgreSQL & SQLAlchemy engine creation and connection pool management."""

import logging
from typing import Any, Dict

from sqlalchemy import Engine, create_engine
from sqlalchemy.pool import NullPool, QueuePool

from app.core.config import get_settings

logger = logging.getLogger(__name__)


def get_engine_options(database_url: str) -> Dict[str, Any]:
    """Build engine options based on database dialect (PostgreSQL vs SQLite)."""
    settings = get_settings()
    options: Dict[str, Any] = {
        "echo": settings.db_echo,
    }

    if database_url.startswith("sqlite"):
        options["connect_args"] = {"check_same_thread": False}
        options["poolclass"] = QueuePool
    elif database_url.startswith("postgresql"):
        options["poolclass"] = QueuePool
        options["pool_size"] = 10
        options["max_overflow"] = 20
        options["pool_timeout"] = 30
        options["pool_recycle"] = 1800
        options["pool_pre_ping"] = True
    else:
        options["pool_pre_ping"] = True

    return options


# pyrefly: ignore [bad-function-definition]
def create_db_engine(database_url: str = None) -> Engine:
    """Create and return a configured SQLAlchemy Engine instance with local SQLite fallback."""
    settings = get_settings()
    url = database_url or settings.database_url

    options = get_engine_options(url)
    logger.info("Initializing SQLAlchemy Engine for dialect: %s", url.split("://")[0])

    try:
        engine = create_engine(url, **options)
        # Test connection immediately
        with engine.connect() as conn:
            pass
        return engine
    except Exception as e:
        logger.warning("Database connection failed for URL %s: %s. Falling back to local SQLite database.", url, e)
        fallback_url = "sqlite:///./cd_se_accelerators.db"
        fallback_options = get_engine_options(fallback_url)
        return create_engine(fallback_url, **fallback_options)
