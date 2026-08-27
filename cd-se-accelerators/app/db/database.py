"""
Database Connection & Session Management – Neon PostgreSQL / SQLAlchemy.

Loads Neon PostgreSQL connection URL from app/.env or environment variables.
Provides SQLAlchemy engine, session maker, Base declarative model, and dependency generators.
Includes safe connection fallback and automatic table creation.
"""

import os
import logging
from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

logger = logging.getLogger(__name__)

# Load .env manually if needed
ENV_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")
def _load_env_url() -> str:
    # 1. Environment variable
    url = os.getenv("NEON_URL") or os.getenv("neon_url") or os.getenv("DATABASE_URL")
    if url:
        return url.strip()

    # 2. app/.env file
    if os.path.exists(ENV_FILE):
        try:
            with open(ENV_FILE, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line.startswith("neon_url=") or line.startswith("NEON_URL=") or line.startswith("DATABASE_URL="):
                        val = line.split("=", 1)[1].strip().strip('"').strip("'")
                        if val:
                            return val
        except Exception as exc:
            logger.warning("Error reading app/.env: %s", exc)

    return ""

DATABASE_URL = _load_env_url()

# Fallback to local SQLite file in temp directory if PostgreSQL is unreachable or unconfigured
if not DATABASE_URL:
    db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "app_database.db")
    DATABASE_URL = f"sqlite:///{db_path}"
    logger.info("Using SQLite fallback database: %s", DATABASE_URL)
else:
    # Ensure postgresql:// scheme for SQLAlchemy compatibility
    if DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
    logger.info("Using Neon PostgreSQL database URL: %s", DATABASE_URL.split("@")[-1] if "@" in DATABASE_URL else "configured")

# Configure engine arguments based on driver
engine_kwargs = {}
if "sqlite" in DATABASE_URL:
    engine_kwargs["connect_args"] = {"check_same_thread": False}
else:
    engine_kwargs["pool_pre_ping"] = True
    engine_kwargs["pool_recycle"] = 300

try:
    engine = create_engine(DATABASE_URL, **engine_kwargs)
except Exception as exc:
    logger.error("Failed creating database engine with primary URL (%s). Falling back to SQLite: %s", exc, DATABASE_URL)
    db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "app_database.db")
    DATABASE_URL = f"sqlite:///{db_path}"
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db() -> Generator:
    """FastAPI dependency yielding a database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """Initialize all database tables defined in Base models."""
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables initialized successfully.")
    except Exception as exc:
        logger.error("Error creating database tables: %s", exc)
