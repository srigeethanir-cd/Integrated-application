from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, validator

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

@app.post("/register")
async def register_member(member_request: MemberRegistrationRequest):
    try:
        # Save member to database
        # For demonstration purposes, this is omitted
        return {"message": "Member registered successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))