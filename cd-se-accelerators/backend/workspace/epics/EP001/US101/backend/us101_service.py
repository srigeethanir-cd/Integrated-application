from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, validator
from typing import Optional
import re

app = FastAPI()

class User(BaseModel):
    email: str

    @validator('email')
    def validate_email(cls, v):
        if not re.match(r"[^@]+@[^@]+\.[^@]+", v):
            raise ValueError('Invalid email format')
        return v

@app.post("/auth/register")
async def create_user(user: User):
    try:
        # Save user to database
        # For demonstration purposes, we'll just return the user
        return user
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/auth/validate-email")
async def validate_email(email: str):
    try:
        User(email=email)
        return {"message": "Email is valid"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))