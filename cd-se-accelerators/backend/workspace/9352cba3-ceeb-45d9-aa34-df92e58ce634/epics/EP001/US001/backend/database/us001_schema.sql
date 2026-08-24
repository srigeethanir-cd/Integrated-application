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
    name = Column(String)
    email = Column(String, unique=True)
    password = Column(String)

# Create all tables in the engine
Base.metadata.create_all(engine)

# models.py
from pydantic import BaseModel
from typing import Optional

class UserRegistration(BaseModel):
    name: str
    email: str
    password: str

class UserResponse(BaseModel):
    id: int
    name: str
    email: str

# main.py
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from fastapi.requests import Request
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from database import Session, User
from models import UserRegistration, UserResponse
from pydantic import ValidationError
from sqlalchemy.exc import IntegrityError
from passlib.context import CryptContext

app = FastAPI()

# Password context
pwd_context = CryptContext(schemes=["bcrypt"], default="bcrypt")

# Register a new user
@app.post("/register")
async def register_user(user_registration: UserRegistration):
    try:
        # Create a new session
        session = Session()
        
        # Check if the email already exists
        existing_user = session.query(User).filter(User.email == user_registration.email).first()
        if existing_user:
            raise HTTPException(status_code=400, detail="Email already exists")
        
        # Hash the password
        hashed_password = pwd_context.hash(user_registration.password)
        
        # Create a new user
        new_user = User(name=user_registration.name, email=user_registration.email, password=hashed_password)
        
        # Add the new user to the session
        session.add(new_user)
        
        # Commit the changes
        session.commit()
        
        # Return the new user
        return UserResponse(id=new_user.id, name=new_user.name, email=new_user.email)
    
    except IntegrityError as e:
        raise HTTPException(status_code=400, detail="Email already exists")
    
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")

    finally:
        # Close the session
        session.close()