# app/main.py
from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from pydantic import BaseModel, validator
from passlib.context import CryptContext
from typing import Optional

app = FastAPI()

# Define the password context
pwd_context = CryptContext(schemes=["bcrypt"], default="bcrypt")

# Define the user model
class User(BaseModel):
    email: str
    password: str

    @validator('email')
    def validate_email(cls, v):
        if '@' not in v:
            raise ValueError('Invalid email format')
        return v

# Define the login request model
class LoginRequest(BaseModel):
    email: str
    password: str

    @validator('email')
    def validate_email(cls, v):
        if '@' not in v:
            raise ValueError('Invalid email format')
        return v

# Define the login response model
class LoginResponse(BaseModel):
    token: str

# Define the in-memory user database
users = {}

# Define the basic auth scheme
security = HTTPBasic()

# Create a new user
@app.post("/users/")
def create_user(user: User):
    # Hash the password
    hashed_password = pwd_context.hash(user.password)
    # Store the user in the in-memory database
    users[user.email] = hashed_password
    return {"message": "User created successfully"}

# Login endpoint
@app.post("/login/")
def login(login_request: LoginRequest):
    # Get the user from the in-memory database
    user = users.get(login_request.email)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    # Verify the password
    if not pwd_context.verify(login_request.password, user):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    # Generate a token
    token = "example_token"
    return {"token": token}

# Protected endpoint
@app.get("/protected/")
def protected(credentials: HTTPBasicCredentials = Depends(security)):
    # Get the user from the in-memory database
    user = users.get(credentials.username)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    # Verify the password
    if not pwd_context.verify(credentials.password, user):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    return {"message": "Hello, authenticated user"}