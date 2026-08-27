from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, EmailStr, Field
from .register_service import register_user

router = APIRouter(prefix="/api/v1/auth", tags=["Authentication"])

class RegisterRequest(BaseModel):
    name: str
    email: EmailStr
    password: str = Field(..., min_length=8)

@router.post("/register", status_code=status.HTTP_201_CREATED)
def register(req: RegisterRequest):
    return register_user(req.name, req.email, req.password)
