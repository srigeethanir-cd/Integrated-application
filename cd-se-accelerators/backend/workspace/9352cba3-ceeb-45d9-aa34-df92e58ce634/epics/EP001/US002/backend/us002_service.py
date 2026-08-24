from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from pydantic import BaseModel
from typing import Dict

app = FastAPI()

# Define the user model
class User(BaseModel):
    username: str
    password: str

# In-memory user storage for demonstration purposes
users: Dict[str, User] = {
    "user1": User(username="user1", password="password1"),
    "user2": User(username="user2", password="password2"),
}

# Define the security scheme
security = HTTPBasic()

# Define the login endpoint
@app.post("/login")
async def login(credentials: HTTPBasicCredentials = Depends(security)):
    # Check if the user exists
    if credentials.username not in users:
        raise HTTPException(status_code=401, detail="Invalid username or password")

    # Check if the password is correct
    if credentials.password != users[credentials.username].password:
        raise HTTPException(status_code=401, detail="Invalid username or password")

    # Return a success message
    return {"message": "Login successful"}

# Define a protected endpoint
@app.get("/dashboard")
async def dashboard(credentials: HTTPBasicCredentials = Depends(security)):
    # Check if the user exists
    if credentials.username not in users:
        raise HTTPException(status_code=401, detail="Invalid username or password")

    # Check if the password is correct
    if credentials.password != users[credentials.username].password:
        raise HTTPException(status_code=401, detail="Invalid username or password")

    # Return the dashboard
    return {"message": "Welcome to your dashboard"}