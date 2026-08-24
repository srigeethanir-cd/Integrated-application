# app/main.py
from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from pydantic import BaseModel, validator
from typing import Optional
import re
import bcrypt

app = FastAPI()

# Define the security scheme
security = HTTPBasic()

# Define the user model
class User(BaseModel):
    email: str
    password: str

    @validator('email')
    def validate_email(cls, v):
        if not re.match(r"[^@]+@[^@]+\.[^@]+", v):
            raise ValueError("Invalid email format")
        return v

# In-memory user storage (replace with a database in production)
users = {}

# Create a new user
@app.post("/users/")
async def create_user(user: User):
    # Check if the user already exists
    if user.email in users:
        raise HTTPException(status_code=400, detail="User already exists")

    # Hash the password
    hashed_password = bcrypt.hashpw(user.password.encode('utf-8'), bcrypt.gensalt())

    # Store the user
    users[user.email] = hashed_password

    return {"message": "User created successfully"}

# Login endpoint
@app.get("/login/")
async def login(credentials: HTTPBasicCredentials = Depends(security)):
    # Check if the user exists
    if credentials.username not in users:
        raise HTTPException(status_code=401, detail="Invalid email or password")

    # Check if the password is correct
    if not bcrypt.checkpw(credentials.password.encode('utf-8'), users[credentials.username]):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    return {"message": "Login successful"}