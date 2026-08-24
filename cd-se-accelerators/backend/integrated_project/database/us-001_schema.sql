python
# models.py
from pydantic import BaseModel, EmailStr
from typing import Optional

class User(BaseModel):
    id: Optional[int]
    email: EmailStr
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str