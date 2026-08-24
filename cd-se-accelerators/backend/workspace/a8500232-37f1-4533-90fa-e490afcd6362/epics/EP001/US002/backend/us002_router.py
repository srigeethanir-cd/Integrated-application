from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from pydantic import BaseModel
from typing import Optional

app = FastAPI()

# Define the user model
class User(BaseModel):
    username: str
    password: str

# In-memory user storage for demonstration purposes
users = {
    "user1": "password1",
    "user2": "password2"
}

# Define the login endpoint
@app.post("/login")
async def login(credentials: HTTPBasicCredentials):
    if credentials.username in users and users[credentials.username] == credentials.password:
        return {"message": "Login successful"}
    else:
        raise HTTPException(status_code=401, detail="Invalid credentials")

# Define a protected route
@app.get("/dashboard")
async def dashboard(credentials: HTTPBasicCredentials = Depends()):
    if credentials.username in users and users[credentials.username] == credentials.password:
        return {"message": "Welcome to your dashboard"}
    else:
        raise HTTPException(status_code=401, detail="Invalid credentials")