# models.py
from pydantic import BaseModel, EmailStr
from typing import Optional

class User(BaseModel):
    id: int
    email: EmailStr
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None