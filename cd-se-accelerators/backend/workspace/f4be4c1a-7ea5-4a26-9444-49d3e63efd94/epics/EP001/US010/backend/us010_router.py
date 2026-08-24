# app/main.py
from fastapi import FastAPI, Response, Request, status
from fastapi.responses import RedirectResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel

app = FastAPI()

# Define the token bearer
security = HTTPBearer()

# Define the user session
class UserSession(BaseModel):
    user_id: str
    token: str

# In-memory user sessions for demonstration purposes
user_sessions = {}

# Login endpoint for demonstration purposes
@app.post("/login")
async def login(username: str, password: str):
    # Replace with actual authentication logic
    user_id = username
    token = "example_token"
    user_sessions[token] = UserSession(user_id=user_id, token=token)
    return {"token": token}

# Logout endpoint
@app.post("/logout")
async def logout(token: HTTPAuthorizationCredentials = Depends(security)):
    # Invalidate the session
    if token.credentials in user_sessions:
        del user_sessions[token.credentials]
    # Redirect to the login page
    return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)

# Example protected route
@app.get("/protected")
async def protected(token: HTTPAuthorizationCredentials = Depends(security)):
    if token.credentials in user_sessions:
        return {"message": "Hello, authenticated user!"}
    else:
        return Response(status_code=status.HTTP_401_UNAUTHORIZED)