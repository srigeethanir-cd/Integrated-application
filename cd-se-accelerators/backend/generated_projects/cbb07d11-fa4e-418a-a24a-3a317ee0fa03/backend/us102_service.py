from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, validator
from typing import Optional
from hashlib import sha256
from hmac import compare_digest

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
registered_members = {}

@app.post("/register", response_model=MemberRegistrationResponse)
async def register_member(member_registration_request: MemberRegistrationRequest):
    if member_registration_request.username in registered_members:
        raise HTTPException(status_code=400, detail="Username already exists")

    # Hash the password for secure storage
    hashed_password = sha256(member_registration_request.password.encode()).hexdigest()

    # Store the member details securely
    registered_members[member_registration_request.username] = {
        "email": member_registration_request.email,
        "password": hashed_password
    }

    return MemberRegistrationResponse(
        username=member_registration_request.username,
        email=member_registration_request.email
    )

@app.get("/members/{username}")
async def get_member(username: str):
    if username not in registered_members:
        raise HTTPException(status_code=404, detail="Member not found")

    member = registered_members[username]
    return {
        "username": username,
        "email": member["email"]
    }