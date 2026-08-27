"""Business logic for the migrated Authentication module."""

from app.core.exceptions import NotFoundError
from app.models.authentication import AuthenticationRecord
from app.repository.authentication_repository import AuthenticationRepository
from app.schemas.authentication import AuthenticationCreate, AuthenticationUpdate


class AuthenticationService:
    def __init__(self, repository: AuthenticationRepository) -> None:
        self.repository = repository

    def list(self, page: int, page_size: int) -> tuple[list[AuthenticationRecord], int]:
        return self.repository.list(offset=(page - 1) * page_size, limit=page_size)

    def get(self, record_id: str) -> AuthenticationRecord:
        record = self.repository.get(record_id)
        if record is None:
            raise NotFoundError("Authentication record")
        return record

    def create(self, payload: AuthenticationCreate) -> AuthenticationRecord:
        return self.repository.save(AuthenticationRecord(**payload.model_dump()))

    def update(self, record_id: str, payload: AuthenticationUpdate) -> AuthenticationRecord:
        record = self.get(record_id)
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(record, field, value)
        return self.repository.save(record)

    def delete(self, record_id: str) -> None:
        self.repository.delete(self.get(record_id))
