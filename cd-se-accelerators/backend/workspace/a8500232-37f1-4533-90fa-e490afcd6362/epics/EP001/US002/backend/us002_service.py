from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from pydantic import BaseModel
from typing import Optional

app = FastAPI()

# Define the user model
class User(BaseModel):
    username: str
    password: str

# In-memory user database for demonstration purposes
users_db = {
    "user1": "password1",
    "user2": "password2",
}

# Define the login endpoint
security = HTTPBasic()

async def get_current_user(credentials: HTTPBasicCredentials = Depends(security)):
    if credentials.username in users_db and users_db[credentials.username] == credentials.password:
        return credentials.username
    else:
        raise HTTPException(
            status_code=401,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": "Basic"},
        )

# Define the login route
@app.get("/login")
async def login(user: str = Depends(get_current_user)):
    return {"message": f"Welcome, {user}!"}

# Define the dashboard route
@app.get("/dashboard")
async def dashboard(user: str = Depends(get_current_user)):
    return {"message": f"Welcome to your dashboard, {user}!"}