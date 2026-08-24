# app/main.py
from fastapi import FastAPI, Response, Request, status
from fastapi.responses import RedirectResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel

app = FastAPI()

class User(BaseModel):
    username: str
    session_id: str

# In-memory session store for demonstration purposes only.
# In a real application, use a secure session store like Redis or a database.
session_store = {}

# Authentication scheme using HTTP Bearer tokens
security = HTTPBearer()

# Create a new session
@app.post("/login")
async def login(username: str, password: str):
    # Replace with your actual authentication logic
    if username == "test" and password == "test":
        session_id = "1234567890"
        session_store[session_id] = username
        return {"session_id": session_id}
    else:
        return Response(status_code=status.HTTP_401_UNAUTHORIZED)

# Logout endpoint
@app.post("/logout")
async def logout(request: Request, credentials: HTTPAuthorizationCredentials = Depends(security)):
    session_id = credentials.credentials
    if session_id in session_store:
        del session_store[session_id]
        return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)
    else:
        return Response(status_code=status.HTTP_401_UNAUTHORIZED)