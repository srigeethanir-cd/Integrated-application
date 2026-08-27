"""Database access for authentication records."""

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from database_main.models.authentication import AuthenticationRecord


class AuthenticationRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def list(self, offset: int, limit: int) -> tuple[list[AuthenticationRecord], int]:
        records = self.session.scalars(
            select(AuthenticationRecord)
            .order_by(AuthenticationRecord.created_at.desc())
            .offset(offset)
            .limit(limit)
        ).all()
        total = self.session.scalar(select(func.count()).select_from(AuthenticationRecord)) or 0
        # pyrefly: ignore [bad-return]
        return records, total

    def get(self, record_id: str) -> AuthenticationRecord | None:
        return self.session.get(AuthenticationRecord, record_id)

    def save(self, record: AuthenticationRecord) -> AuthenticationRecord:
        self.session.add(record)
        self.session.commit()
        self.session.refresh(record)
        return record

    def delete(self, record: AuthenticationRecord) -> None:
        self.session.delete(record)
        self.session.commit()
