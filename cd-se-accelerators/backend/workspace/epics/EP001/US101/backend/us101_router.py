from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel, validator
from typing import Optional
from email_validator import validate_email, EmailNotValidError

app = FastAPI()

class User(BaseModel):
    email: str

    @validator('email')
    def validate_email(cls, v):
        try:
            validate_email(v)
            return v
        except EmailNotValidError as e:
            raise ValueError("Invalid email format") from e

class AuthPortal:
    def __init__(self):
        self.users = []

    def create_user(self, user: User):
        self.users.append(user)
        return user

auth_portal = AuthPortal()

@app.post("/users/")
async def create_user(user: User):
    try:
        created_user = auth_portal.create_user(user)
        return created_user
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))