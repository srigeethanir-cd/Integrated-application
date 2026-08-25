from typing import Protocol

from sqlalchemy import select
from sqlalchemy.orm import Session

from .models import User


class UserRepositoryProtocol(Protocol):
    def get_by_id(self, user_id: int) -> User | None: ...
    def get_by_email(self, email: str) -> User | None: ...
    def add(self, user: User) -> User: ...
    def delete(self, user: User) -> None: ...
    def search(self, query: str, limit: int) -> list[User]: ...


class UserRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_id(self, user_id: int) -> User | None:
        return self.db.get(User, user_id)

    def get_by_email(self, email: str) -> User | None:
        return self.db.scalar(select(User).where(User.email == email))

    def add(self, user: User) -> User:
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def delete(self, user: User) -> None:
        self.db.delete(user)
        self.db.commit()

    def search(self, query: str, limit: int) -> list[User]:
        statement = select(User).where(User.email.contains(query)).order_by(User.email).limit(limit)
        return list(self.db.scalars(statement))

