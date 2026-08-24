from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from pydantic import BaseModel
from typing import Optional
from passlib.context import CryptContext
from jose import jwt, JWTError
from datetime import datetime, timedelta
import re

# Initialize FastAPI app
app = FastAPI()

# Initialize security
security = HTTPBasic()

# Initialize password context
pwd_context = CryptContext(schemes=["bcrypt"], default="bcrypt")

# Initialize secret key for JWT
SECRET_KEY = "your_secret_key_here"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Define email validation regex
EMAIL_REGEX = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"

# Define user model
class User(BaseModel):
    email: str
    password: str

# Define token model
class Token(BaseModel):
    access_token: str
    token_type: str

# Define token data model
class TokenData(BaseModel):
    email: Optional[str] = None

# Function to validate email format
def validate_email_format(email: str):
    if not re.match(EMAIL_REGEX, email):
        raise HTTPException(status_code=400, detail="Invalid email format")
    return email

# Function to secure password field input
def secure_password_field_input(password: str):
    if len(password) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters long")
    return pwd_context.hash(password)

# Function to verify password
def verify_password(plain_password: str, hashed_password: str):
    return pwd_context.verify(plain_password, hashed_password)

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
    return token_data.email

# Route to login
@app.post("/login")
async def login(user: User):
    # Validate email format
    validate_email_format(user.email)
    
    # Secure password field input
    # For demonstration purposes, assume the password is stored in a database
    # In a real application, you would query the database to retrieve the stored password
    stored_password = secure_password_field_input("your_stored_password_here")
    
    # Verify password
    if not verify_password(user.password, stored_password):
        raise HTTPException(status_code=401, detail="Invalid password")
    
    # Create access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    
    # Return token
    return {"access_token": access_token, "token_type": "bearer"}

# Route to protected route
@app.get("/protected")
async def protected_route(current_user: str = Depends(get_current_user)):
    return {"message": f"Hello, {current_user}!"}