from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from passlib.context import CryptContext
from sqlalchemy import create_engine, Column, String, Integer
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from typing import List

# Database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///example.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# Define the User model
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    email = Column(String, unique=True, index=True)
    password = Column(String)

# Create the database tables
Base.metadata.create_all(bind=engine)

# Define the User schema
class UserSchema(BaseModel):
    name: str
    email: str
    password: str

# Define the User response schema
class UserResponseSchema(BaseModel):
    id: int
    name: str
    email: str

# Initialize the FastAPI app
app = FastAPI()

# Initialize the password context
pwd_context = CryptContext(schemes=["bcrypt"], default="bcrypt")

# Define the dependency to get the database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Define the endpoint to register a new user
@app.post("/register", response_model=UserResponseSchema)
async def register_user(user: UserSchema, db = Depends(get_db)):
    # Check if the email is already in use
    existing_user = db.query(User).filter(User.email == user.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already in use")

    # Hash the password
    hashed_password = pwd_context.hash(user.password)

    # Create a new user
    new_user = User(name=user.name, email=user.email, password=hashed_password)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # Return the new user
    return new_user