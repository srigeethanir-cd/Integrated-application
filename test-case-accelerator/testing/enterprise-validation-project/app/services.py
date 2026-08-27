from .auth import create_access_token, hash_password, verify_password
from .exceptions import EmailConflict, InvalidCredentials, UserNotFound
from .models import User
from .repositories import UserRepositoryProtocol
from .schemas import UserCreate, UserUpdate


class UserService:
    def __init__(self, repository: UserRepositoryProtocol) -> None:
        self.repository = repository

    def create_user(self, payload: UserCreate) -> User:
        if self.repository.get_by_email(str(payload.email)):
            raise EmailConflict()
        user = User(email=str(payload.email), hashed_password=hash_password(payload.password))
        return self.repository.add(user)

    def login(self, email: str, password: str) -> str:
        user = self.authenticate_user(email, password)
        return create_access_token(str(user.id))

    def authenticate_user(self, email: str, password: str) -> User:
        user = self.repository.get_by_email(email)
        if user is None or not user.is_active or not verify_password(password, user.hashed_password):
            raise InvalidCredentials()
        return user

    def get_dashboard(self, user_id: int) -> dict[str, object]:
        user = self.repository.get_by_id(user_id)
        if user is None:
            raise UserNotFound()
        return {"user_id": user.id, "email": user.email, "active": user.is_active}

    def update_user(self, user_id: int, payload: UserUpdate) -> User:
        user = self.repository.get_by_id(user_id)
        if user is None:
            raise UserNotFound()
        if payload.email is not None:
            user.email = str(payload.email)
        if payload.is_active is not None:
            user.is_active = payload.is_active
        return self.repository.add(user)

    def delete_user(self, user_id: int) -> bool:
        user = self.repository.get_by_id(user_id)
        if user is None:
            raise UserNotFound()
        self.repository.delete(user)
        return True

    def search_users(self, query: str, limit: int = 20) -> list[User]:
        if not 1 <= limit <= 100:
            raise ValueError("limit must be between 1 and 100")
        return self.repository.search(query.strip().lower(), limit)

    def reset_password(self, user_id: int, new_password: str) -> User:
        if len(new_password) < 12 or not any(char.isdigit() for char in new_password):
            raise ValueError("password must contain 12 characters and a digit")
        user = self.repository.get_by_id(user_id)
        if user is None:
            raise UserNotFound()
        user.hashed_password = hash_password(new_password)
        return self.repository.add(user)

