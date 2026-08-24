"""Authentication module dependencies."""

from fastapi import Depends
from sqlalchemy.orm import Session

from app.database.session import get_db_session
from app.repository.authentication_repository import AuthenticationRepository
from app.services.authentication_service import AuthenticationService


def get_authentication_service(session: Session = Depends(get_db_session)) -> AuthenticationService:
    return AuthenticationService(AuthenticationRepository(session))
