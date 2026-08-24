python
# models.py
from sqlalchemy import Column, String, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError
from pydantic import BaseModel
from typing import Optional

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    name = Column(String, nullable=False)
    email = Column(String, primary_key=True, unique=True, nullable=False)
    password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)

class UserRegistrationRequest(BaseModel):
    name: str
    email: str
    password: str

class UserRegistrationResponse(BaseModel):
    email: str
    name: str

# database.py
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from models import Base, User

SQLALCHEMY_DATABASE_URL = "sqlite:///example.db"

engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# main.py
from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from database import get_db
from models import User, UserRegistrationRequest, UserRegistrationResponse
from sqlalchemy.exc import IntegrityError
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], default="bcrypt")
security = HTTPBasic()

app = FastAPI()

@app.post("/register", response_model=UserRegistrationResponse)
async def register_user(user_request: UserRegistrationRequest, db = Depends(get_db)):
    hashed_password = pwd_context.hash(user_request.password)
    db_user = User(name=user_request.name, email=user_request.email, password=hashed_password)
    try:
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        return UserRegistrationResponse(email=db_user.email, name=db_user.name)
    except IntegrityError:
        raise HTTPException(status_code=400, detail="Email already registered")