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
async def register_member(member_registration_request: MemberRegistrationRequest):
    try:
        # Here you would typically save the user to a database
        # For this example, we'll just return the request
        return member_registration_request
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))