# app/main.py
from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from typing import List
from passlib.context import CryptContext
from jose import jwt, JWTError
from datetime import datetime, timedelta

# Initialize FastAPI app
app = FastAPI()

# Initialize database connection
SQLALCHEMY_DATABASE_URL = "sqlite:///user.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# Define user model
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    password = Column(String)

# Create database tables
Base.metadata.create_all(bind=engine)

# Define user registration request model
class UserRegistrationRequest(BaseModel):
    username: str
    email: str
    password: str

# Define user registration response model
class UserRegistrationResponse(BaseModel):
    id: int
    username: str
    email: str

# Initialize password context
pwd_context = CryptContext(schemes=["bcrypt"], default="bcrypt")

# Initialize JWT secret key
SECRET_KEY = "secret_key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Define function to verify password
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

# Define function to get password hash
def get_password_hash(password):
    return pwd_context.hash(password)

# Define function to create access token
def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# Define function to get current user
async def get_current_user(token: str = Depends()):
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    db = SessionLocal()
    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise credentials_exception
    return user

# Define user registration endpoint
@app.post("/register", response_model=UserRegistrationResponse)
async def register_user(user_registration_request: UserRegistrationRequest):
    db = SessionLocal()
    existing_user = db.query(User).filter(User.username == user_registration_request.username).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already exists")
    existing_email = db.query(User).filter(User.email == user_registration_request.email).first()
    if existing_email:
        raise HTTPException(status_code=400, detail="Email already exists")
    new_user = User(
        username=user_registration_request.username,
        email=user_registration_request.email,
        password=get_password_hash(user_registration_request.password)
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": new_user.username}, expires_delta=access_token_expires
    )
    return {
        "id": new_user.id,
        "username": new_user.username,
        "email": new_user.email,
        "access_token": access_token,
        "token_type": "bearer"
    }