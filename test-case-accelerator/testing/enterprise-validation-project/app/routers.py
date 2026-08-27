from fastapi import APIRouter, Depends, Query, status

from .dependencies import get_user_service
from .schemas import LoginRequest, UserCreate, UserResponse, UserUpdate
from .services import UserService

router = APIRouter(prefix="/users", tags=["users"])


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(payload: UserCreate, service: UserService = Depends(get_user_service)):
    return service.create_user(payload)


@router.post("/login")
def login(payload: LoginRequest, service: UserService = Depends(get_user_service)):
    return {"access_token": service.login(str(payload.email), payload.password), "token_type": "bearer"}


@router.get("/{user_id}/dashboard")
def get_dashboard(user_id: int, service: UserService = Depends(get_user_service)):
    return service.get_dashboard(user_id)


@router.patch("/{user_id}", response_model=UserResponse)
def update_user(user_id: int, payload: UserUpdate, service: UserService = Depends(get_user_service)):
    return service.update_user(user_id, payload)


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(user_id: int, service: UserService = Depends(get_user_service)):
    service.delete_user(user_id)


@router.get("", response_model=list[UserResponse])
def search_users(query: str = Query(min_length=1, max_length=100), limit: int = Query(20, ge=1, le=100), service: UserService = Depends(get_user_service)):
    return service.search_users(query, limit)

