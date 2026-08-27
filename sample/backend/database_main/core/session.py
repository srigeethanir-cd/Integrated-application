"""SQLAlchemy 2.x session handling and lifecycle management."""

from contextlib import contextmanager
from typing import Generator

from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings
from database_main.core.base import Base
from database_main.core.connection import create_db_engine

settings = get_settings()
engine = create_db_engine()

SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
)


class DatabaseSessionManager:
    """Manages database session initialization and scope context."""

    def __init__(self, session_factory: sessionmaker = None):
        self.session_factory = session_factory or SessionLocal

    def get_session(self) -> Session:
        """Create a new database session."""
        return self.session_factory()

    @contextmanager
    def session_scope(self) -> Generator[Session, None, None]:
        """Provide a transactional scope around a series of operations.
        
        Designed for LangGraph nodes, background tasks, and agent executions.
        """
        session = self.get_session()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()


session_manager = DatabaseSessionManager()


def get_db() -> Generator[Session, None, None]:
    """FastAPI request-scoped database session dependency."""
    session = SessionLocal()
    try:
        yield session
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


# Alias for backward compatibility
get_db_session = get_db
