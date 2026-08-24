from fastapi import FastAPI, Response, Request, status
from fastapi.responses import RedirectResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel

app = FastAPI()

# Define a route for logout
@app.post("/logout")
async def logout(request: Request):
    # Get the session
    session = request.session
    
    # Invalidate the session
    session.clear()
    
    # Redirect to the login page
    return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)

# Define a route for login (for testing purposes)
@app.get("/login")
async def login():
    return {"message": "Login page"}

# Define a route for protected pages (for testing purposes)
@app.get("/protected")
async def protected(request: Request):
    # Check if the user is logged in
    if not request.session.get("user"):
        return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)
    
    return {"message": "Protected page"}

# Run the application
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)