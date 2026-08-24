python
# models.py
from pydantic import BaseModel, EmailStr, validator
from typing import Optional

class MemberLogin(BaseModel):
    email: EmailStr
    password: str

    @validator('email')
    def validate_email(cls, v):
        # Validate email format
        if not v:
            raise ValueError('Email is required')
        return v

    @validator('password')
    def validate_password(cls, v):
        # Secure password field input
        if not v:
            raise ValueError('Password is required')
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        return v

# schemas.py
from pydantic import BaseModel
from typing import Optional

class MemberLoginResponse(BaseModel):
    email: str
    message: str

# database.py
from sqlalchemy import create_engine, Column, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

SQLALCHEMY_DATABASE_URL = "sqlite:///member_login.db"

engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

class MemberLoginModel(Base):
    __tablename__ = "member_login"
    email = Column(String, primary_key=True, index=True)
    password = Column(String, index=True)

Base.metadata.create_all(bind=engine)

# main.py
from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from pydantic import BaseModel
from sqlalchemy.orm import Session
from database import SessionLocal, MemberLoginModel
from models import MemberLogin
from schemas import MemberLoginResponse
from typing import Optional

app = FastAPI()

security = HTTPBasic()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/login", response_model=MemberLoginResponse)
def login(member_login: MemberLogin, db: Session = Depends(get_db)):
    # Validate email format and secure password field input
    try:
        # Check if member exists
        member = db.query(MemberLoginModel).filter(MemberLoginModel.email == member_login.email).first()
        if not member:
            raise HTTPException(status_code=401, detail="Invalid email or password")
        
        # Check if password is correct
        if member.password != member_login.password:
            raise HTTPException(status_code=401, detail="Invalid email or password")
        
        return {"email": member_login.email, "message": "Login successful"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/register", response_model=MemberLoginResponse)
def register(member_login: MemberLogin, db: Session = Depends(get_db)):
    # Validate email format and secure password field input
    try:
        # Check if member already exists
        member = db.query(MemberLoginModel).filter(MemberLoginModel.email == member_login.email).first()
        if member:
            raise HTTPException(status_code=400, detail="Email already exists")
        
        # Create new member
        new_member = MemberLoginModel(email=member_login.email, password=member_login.password)
        db.add(new_member)
        db.commit()
        db.refresh(new_member)
        
        return {"email": member_login.email, "message": "Registration successful"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))