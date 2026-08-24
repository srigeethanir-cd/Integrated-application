from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, validator
from passlib.context import CryptContext
from typing import Optional
from datetime import datetime, timedelta
import jwt

# Initialize FastAPI app
app = FastAPI()

# Initialize password context
pwd_context = CryptContext(schemes=["bcrypt"], default="bcrypt")

# Initialize secret key for JWT
secret_key = "your-secret-key"

# Define user model
class User(BaseModel):
    id: Optional[int]
    email: str
    password: str

    @validator("email")
    def validate_email(cls, v):
        if "@" not in v:
            raise ValueError("Invalid email")
        return v

# Define token model
class Token(BaseModel):
    access_token: str
    token_type: str

# Define token data model
class TokenData(BaseModel):
    email: Optional[str] = None

# Define authentication scheme
security = HTTPBearer()

# Function to verify password
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

# Function to get password hash
def get_password_hash(password):
    return pwd_context.hash(password)

# Function to authenticate user
def authenticate_user(email: str, password: str):
    # Replace with your database query to get user by email
    user = User(email=email, password=get_password_hash("your-default-password"))
    if not user:
        return False
    if not verify_password(password, user.password):
        return False
    return user

# Function to create access token
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, secret_key, algorithm="HS256")
    return encoded_jwt

# Register user endpoint
@app.post("/register")
async def register_user(user: User):
    # Replace with your database query to create new user
    # For demonstration purposes, we'll just return the user
    user.password = get_password_hash(user.password)
    return user

# Login user endpoint
@app.post("/login")
async def login_user(email: str, password: str):
    user = authenticate_user(email, password)
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=30)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

# Protected route
@app.get("/users/me")
async def read_users_me(token: HTTPAuthorizationCredentials = Depends(security)):
    token_data = TokenData(email=token.credentials)
    # Replace with your database query to get user by email
    user = User(email=token_data.email, password=get_password_hash("your-default-password"))
    return user