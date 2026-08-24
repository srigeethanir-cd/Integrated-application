python
# database/models.py
from sqlalchemy import Column, String, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError
from pydantic import BaseModel, validator
from typing import Optional

# Define the database connection
SQLALCHEMY_DATABASE_URL = "sqlite:///database.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(String, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    is_active = Column(Boolean, default=True)

Base.metadata.create_all(bind=engine)

class UserRegistrationRequest(BaseModel):
    username: str
    email: str
    password: str
    confirm_password: str

    @validator('confirm_password')
    def passwords_match(cls, v, values, **kwargs):
        if 'password' in values and v != values['password']:
            raise ValueError('Passwords do not match')
        return v

# database/repository.py
from database.models import SessionLocal, User

class UserRepository:
    def __init__(self, db: SessionLocal):
        self.db = db

    def create_user(self, user: UserRegistrationRequest):
        db_user = User(
            id=user.username,
            username=user.username,
            email=user.email,
            hashed_password=user.password  # In a real application, you should hash the password
        )
        try:
            self.db.add(db_user)
            self.db.commit()
            self.db.refresh(db_user)
            return db_user
        except IntegrityError:
            self.db.rollback()
            return None

# main.py
from fastapi import FastAPI, HTTPException
from database.repository import UserRepository
from database.models import UserRegistrationRequest, SessionLocal

app = FastAPI()

@app.post("/register")
async def register_user(user: UserRegistrationRequest):
    db = SessionLocal()
    user_repository = UserRepository(db)
    if user_repository.create_user(user):
        return {"message": "User created successfully"}
    else:
        raise HTTPException(status_code=400, detail="User already exists")