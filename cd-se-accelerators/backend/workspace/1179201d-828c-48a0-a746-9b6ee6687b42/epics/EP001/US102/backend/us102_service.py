from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, validator
from typing import Optional

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
    id: int
    username: str
    email: str

# In-memory data store for demonstration purposes
members = []

@app.post("/register", response_model=MemberRegistrationResponse)
async def register_member(member_request: MemberRegistrationRequest):
    try:
        # Validate password confirmation match
        if member_request.password != member_request.confirm_password:
            raise HTTPException(status_code=400, detail="Passwords do not match")

        # Generate a unique member ID
        member_id = len(members) + 1

        # Create a new member
        member = {
            "id": member_id,
            "username": member_request.username,
            "email": member_request.email,
        }

        # Add the new member to the data store
        members.append(member)

        # Return the registered member details
        return MemberRegistrationResponse(id=member_id, username=member_request.username, email=member_request.email)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))