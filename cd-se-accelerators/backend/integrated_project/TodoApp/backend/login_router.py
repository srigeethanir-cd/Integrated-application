from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr
from .login_service import authenticate_user

router = APIRouter(prefix="/api/v1/auth", tags=["Authentication"])

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

@router.post("/login")
def login(req: LoginRequest):
    token = authenticate_user(req.email, req.password)
    if not token:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return {"access_token": token, "token_type": "bearer"}
