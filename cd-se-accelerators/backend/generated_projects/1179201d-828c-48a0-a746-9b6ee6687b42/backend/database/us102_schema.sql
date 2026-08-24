python
# models.py
from pydantic import BaseModel, validator
from typing import Optional

class MemberRegistration(BaseModel):
    username: str
    email: str
    password: str
    confirm_password: str

    @validator('confirm_password')
    def passwords_match(cls, v, values, **kwargs):
        if 'password' in values and v != values['password']:
            raise ValueError('Passwords do not match')
        return v

# schemas.py
from pydantic import BaseModel
from typing import Optional

class MemberRegistrationRequest(BaseModel):
    username: str
    email: str
    password: str
    confirm_password: str

class MemberRegistrationResponse(BaseModel):
    id: int
    username: str
    email: str

# database.py
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

SQLALCHEMY_DATABASE_URL = "sqlite:///member_registration.db"

engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

class MemberRegistrationModel(Base):
    __tablename__ = "member_registration"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    password = Column(String)

Base.metadata.create_all(bind=engine)

# crud.py
from database import SessionLocal, MemberRegistrationModel
from models import MemberRegistration

def create_member_registration(db: SessionLocal, member_registration: MemberRegistration):
    db_member_registration = MemberRegistrationModel(
        username=member_registration.username,
        email=member_registration.email,
        password=member_registration.password
    )
    db.add(db_member_registration)
    db.commit()
    db.refresh(db_member_registration)
    return db_member_registration

# main.py
from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from crud import create_member_registration
from schemas import MemberRegistrationRequest, MemberRegistrationResponse
from database import SessionLocal

app = FastAPI()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/member/registration", response_model=MemberRegistrationResponse)
def create_member_registration(member_registration_request: MemberRegistrationRequest, db: SessionLocal = Depends(get_db)):
    try:
        member_registration = MemberRegistration(
            username=member_registration_request.username,
            email=member_registration_request.email,
            password=member_registration_request.password,
            confirm_password=member_registration_request.confirm_password
        )
        db_member_registration = create_member_registration(db, member_registration)
        return MemberRegistrationResponse(
            id=db_member_registration.id,
            username=db_member_registration.username,
            email=db_member_registration.email
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))