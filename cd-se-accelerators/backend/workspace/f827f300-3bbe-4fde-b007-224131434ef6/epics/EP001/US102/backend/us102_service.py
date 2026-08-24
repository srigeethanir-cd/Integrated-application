from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, validator
from typing import Optional
from hashlib import sha256
import secrets

app = FastAPI()

class MemberRegistrationRequest(BaseModel):
    username: str
    email: str
    password: str
    confirm_password: str

    @validator('confirm_password')
    def passwords_match(cls, v, values, **kwargs):
        if 'password' in values and v != values['password']:
            raise ValueError('Passwords do not match')
        return v

class MemberRegistrationResponse(BaseModel):
    username: str
    email: str

# In-memory storage for demonstration purposes only
# In a real application, use a secure database
members = {}

@app.post("/register", response_model=MemberRegistrationResponse)
async def register_member(member_request: MemberRegistrationRequest):
    # Check if member already exists
    if member_request.username in members:
        raise HTTPException(status_code=400, detail="Member already exists")

    # Hash password
    hashed_password = sha256(member_request.password.encode()).hexdigest()
    salt = secrets.token_hex(16)

    # Store member in in-memory storage
    members[member_request.username] = {
        "email": member_request.email,
        "password": hashed_password,
        "salt": salt
    }

    return MemberRegistrationResponse(username=member_request.username, email=member_request.email)