from fastapi import FastAPI, Response, Request, status
from fastapi.responses import RedirectResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel

app = FastAPI()

# Define a route for logging out
@app.post("/logout")
async def logout(request: Request):
    # Get the session
    session = request.session
    
    # Invalidate the session
    session.clear()
    
    # Redirect to the login page
    return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)

# Define a route for the login page
@app.get("/login")
async def login():
    return {"message": "Login page"}

# Define a route to test the logout functionality
@app.get("/protected")
async def protected(request: Request):
    # Get the session
    session = request.session
    
    # Check if the session is empty
    if not session:
        # Redirect to the login page if the session is empty
        return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)
    
    # Return a success message if the session is not empty
    return {"message": "Protected page"}

# Run the application
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)