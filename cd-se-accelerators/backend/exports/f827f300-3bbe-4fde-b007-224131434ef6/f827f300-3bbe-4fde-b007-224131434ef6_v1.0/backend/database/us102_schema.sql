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
SQLALCHEMY_DATABASE_URL = "sqlite:///member.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# Define the Member model
class Member(Base):
    __tablename__ = "members"
    id = Column(String, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    password = Column(String)
    is_active = Column(Boolean, default=True)

# Create the database tables
Base.metadata.create_all(bind=engine)

# Define the Member registration request model
class MemberRegistrationRequest(BaseModel):
    id: str
    email: str
    password: str
    confirm_password: str

    @validator('confirm_password')
    def passwords_match(cls, v, values, **kwargs):
        if 'password' in values and v != values['password']:
            raise ValueError('Passwords do not match')
        return v

# Define the Member registration service
class MemberRegistrationService:
    def __init__(self, db_session):
        self.db_session = db_session

    def register_member(self, member_request: MemberRegistrationRequest):
        try:
            new_member = Member(id=member_request.id, email=member_request.email, password=member_request.password)
            self.db_session.add(new_member)
            self.db_session.commit()
            return new_member
        except IntegrityError:
            self.db_session.rollback()
            raise ValueError("Member with this email already exists")

# Define the FastAPI endpoint for member registration
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse

app = FastAPI()

@app.post("/members/")
async def create_member(member_request: MemberRegistrationRequest):
    db_session = SessionLocal()
    member_service = MemberRegistrationService(db_session)
    try:
        new_member = member_service.register_member(member_request)
        return JSONResponse(content={"message": "Member created successfully"}, status_code=201)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        db_session.close()