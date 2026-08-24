from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from passlib.context import CryptContext
from datetime import datetime, timedelta
from jose import jwt

app = FastAPI()

# Define the user model
class User(BaseModel):
    id: int
    email: str
    password: str

# Define the login request model
class LoginRequest(BaseModel):
    email: str
    password: str

# Define the login response model
class LoginResponse(BaseModel):
    access_token: str
    token_type: str

# Initialize the password context
pwd_context = CryptContext(schemes=["bcrypt"], default="bcrypt")

# Initialize the secret key for JWT
SECRET_KEY = "secret_key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Initialize the user database (in-memory for simplicity)
users = [
    User(id=1, email="user@example.com", password=pwd_context.hash("password")),
]

# Define the authentication scheme
security = HTTPBearer()

# Define the login endpoint
@app.post("/login", response_model=LoginResponse)
async def login(login_request: LoginRequest):
    # Find the user by email
    user = next((user for user in users if user.email == login_request.email), None)
    
    # Check if the user exists and the password is correct
    if user and pwd_context.verify(login_request.password, user.password):
        # Generate an access token
        access_token_expires = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = jwt.encode(
            {"sub": user.email, "exp": access_token_expires},
            SECRET_KEY,
            algorithm=ALGORITHM,
        )
        
        # Return the access token
        return {"access_token": access_token, "token_type": "bearer"}
    else:
        # Raise an exception for invalid credentials
        raise HTTPException(status_code=401, detail="Invalid email or password")

# Define the protected endpoint
@app.get("/protected")
async def protected(token: HTTPAuthorizationCredentials = Depends(security)):
    # Verify the access token
    try:
        payload = jwt.decode(token.credentials, SECRET_KEY, algorithms=[ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Access token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid access token")
    
    # Return a success message
    return {"message": "Hello, authenticated user!"}