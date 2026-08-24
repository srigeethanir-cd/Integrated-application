python
# database.py
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Create a database engine
engine = create_engine('postgresql://user:password@localhost/dbname')

# Create a configured "Session" class
Session = sessionmaker(bind=engine)

# Create a base class for declarative class definitions
Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True)
    email = Column(String, unique=True)
    password = Column(String)

    def __repr__(self):
        return f"User(id={self.id}, username='{self.username}', email='{self.email}')"

# Create all tables in the engine
Base.metadata.create_all(engine)

# models.py
from pydantic import BaseModel, validator
from typing import Optional

class UserRegistrationRequest(BaseModel):
    username: str
    email: str
    password: str

    @validator('username')
    def username_must_be_at_least_3_chars(cls, v):
        if len(v) < 3:
            raise ValueError('Username must be at least 3 characters')
        return v

    @validator('email')
    def email_must_be_valid(cls, v):
        if '@' not in v:
            raise ValueError('Invalid email address')
        return v

    @validator('password')
    def password_must_be_at_least_8_chars(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters')
        return v

class UserRegistrationResponse(BaseModel):
    id: int
    username: str
    email: str

# main.py
from fastapi import FastAPI, HTTPException
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from pydantic import BaseModel
from database import Session, User
from models import UserRegistrationRequest, UserRegistrationResponse
from passlib.context import CryptContext

app = FastAPI()

# Set up password hashing
pwd_context = CryptContext(schemes=["bcrypt"], default="bcrypt")

# Set up basic auth
security = HTTPBasic()

@app.post("/register")
async def register_user(user_request: UserRegistrationRequest):
    # Check if user already exists
    session = Session()
    existing_user = session.query(User).filter_by(username=user_request.username).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already taken")

    # Hash password
    hashed_password = pwd_context.hash(user_request.password)

    # Create new user
    new_user = User(username=user_request.username, email=user_request.email, password=hashed_password)
    session.add(new_user)
    session.commit()
    session.refresh(new_user)

    # Return user details
    return UserRegistrationResponse(id=new_user.id, username=new_user.username, email=new_user.email)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)