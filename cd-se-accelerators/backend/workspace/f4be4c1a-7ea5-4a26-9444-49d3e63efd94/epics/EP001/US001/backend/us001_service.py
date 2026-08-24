from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from pydantic import BaseModel
from typing import Optional
from passlib.context import CryptContext
from sqlalchemy import create_engine, Column, String, Integer
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Initialize FastAPI app
app = FastAPI()

# Initialize database connection
SQLALCHEMY_DATABASE_URL = "sqlite:///example.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# Define user model
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    email = Column(String, unique=True, index=True)
    password = Column(String)

# Create database tables
Base.metadata.create_all(bind=engine)

# Define password context
pwd_context = CryptContext(schemes=["bcrypt"], default="bcrypt")

# Define user registration request model
class UserRegistrationRequest(BaseModel):
    name: str
    email: str
    password: str

# Define user registration response model
class UserRegistrationResponse(BaseModel):
    id: int
    name: str
    email: str

# Dependency to get database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Register user endpoint
@app.post("/register", response_model=UserRegistrationResponse)
async def register_user(user_registration_request: UserRegistrationRequest, db = Depends(get_db)):
    # Check if email already exists
    existing_user = db.query(User).filter(User.email == user_registration_request.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already exists")

    # Hash password
    hashed_password = pwd_context.hash(user_registration_request.password)

    # Create new user
    new_user = User(
        name=user_registration_request.name,
        email=user_registration_request.email,
        password=hashed_password
    )

    # Add new user to database
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # Return registered user
    return UserRegistrationResponse(
        id=new_user.id,
        name=new_user.name,
        email=new_user.email
    )