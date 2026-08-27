from fastapi import Depends
from sqlalchemy.orm import Session

from .database import get_db
from .repositories import UserRepository
from .services import UserService


def get_user_service(db: Session = Depends(get_db)) -> UserService:
    return UserService(UserRepository(db))

