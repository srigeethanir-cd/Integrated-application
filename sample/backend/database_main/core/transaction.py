"""Transaction management and Unit of Work abstractions."""

from contextlib import contextmanager
from typing import Generator

from sqlalchemy.orm import Session


class TransactionManager:
    """Manages transactional boundaries and atomic commits across repositories."""

    def __init__(self, db: Session):
        self.db = db

    def commit(self) -> None:
        """Commit current transaction."""
        self.db.commit()

    def rollback(self) -> None:
        """Rollback current transaction."""
        self.db.rollback()

    @contextmanager
    def begin_nested(self) -> Generator[Session, None, None]:
        """Begin a nested transaction (savepoint)."""
        savepoint = self.db.begin_nested()
        try:
            yield self.db
            savepoint.commit()
        except Exception:
            savepoint.rollback()
            raise

    @contextmanager
    def transaction(self) -> Generator[Session, None, None]:
        """Provide atomic transaction boundary."""
        try:
            yield self.db
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise
