# user_registration.py
from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr, validator
from passlib.context import CryptContext
from typing import Optional
from jose import jwt, JWTError
from datetime import datetime, timedelta

# Initialize FastAPI app
app = FastAPI()

# Define password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], default="bcrypt")

# Define user model
class User(BaseModel):
    id: Optional[int]
    email: EmailStr
    password: str

    @validator("email")
    def validate_email(cls, v):
        if not v:
            raise ValueError("Email is required")
        return v

    @validator("password")
    def validate_password(cls, v):
        if not v:
            raise ValueError("Password is required")
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        return v

# Define token model
class Token(BaseModel):
    access_token: str
    token_type: str

# Define token data model
class TokenData(BaseModel):
    email: Optional[EmailStr] = None

# Define secret key and algorithm for JWT
SECRET_KEY = "your-secret-key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Function to verify password
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

# Function to get password hash
def get_password_hash(password):
    return pwd_context.hash(password)

# Function to create access token
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# Function to get current user
async def get_current_user(token: str = Depends()):
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
        token_data = TokenData(email=email)
    except JWTError:
        raise credentials_exception
    user = User(email=token_data.email)
    return user

# Define route for user registration
@app.post("/register")
async def register_user(user: User):
    # Check if user with same email already exists
    # For demonstration purposes, we assume that the user does not exist
    # In a real application, you would query your database to check for existing users
    existing_user = None
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already in use")

    # Hash user password
    user.password = get_password_hash(user.password)

    # Create access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )

    # Return user and access token
    return {"user": user, "access_token": access_token, "token_type": "bearer"}

# Define route for user login
@app.post("/login")
async def login_user(email: EmailStr, password: str):
    # Check if user exists
    # For demonstration purposes, we assume that the user exists
    # In a real application, you would query your database to check for existing users
    user = User(email=email, password=password)

    # Verify user password
    if not verify_password(password, user.password):
        raise HTTPException(status_code=401, detail="Invalid password")

    # Create access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )

    # Return access token
    return {"access_token": access_token, "token_type": "bearer"}