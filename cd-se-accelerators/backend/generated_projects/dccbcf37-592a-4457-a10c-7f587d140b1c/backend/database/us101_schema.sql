python
# database.py
from fastapi import Depends, FastAPI, HTTPException
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr
from passlib.context import CryptContext
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Database Configuration
SQLALCHEMY_DATABASE_URL = "sqlite:///member.db"

engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# Password Hashing
pwd_context = CryptContext(schemes=["bcrypt"], default="bcrypt")

# Member Model
class Member(Base):
    __tablename__ = "members"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)

    def verify_password(self, plain_password):
        return pwd_context.verify(plain_password, self.hashed_password)

# Create Database Tables
Base.metadata.create_all(bind=engine)

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# FastAPI App
app = FastAPI()

# OAuth2 Scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

# Member Request Model
class MemberRequest(BaseModel):
    email: EmailStr
    password: str

# Login Response Model
class LoginResponse(BaseModel):
    access_token: str
    token_type: str

# Validate Email Format
def validate_email_format(email: str):
    if "@" not in email:
        raise HTTPException(status_code=400, detail="Invalid email format")
    return email

# Secure Password Field Input
def secure_password_field_input(password: str):
    if len(password) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters long")
    return password

# Create Member
@app.post("/members/")
def create_member(member_request: MemberRequest, db = Depends(get_db)):
    validate_email_format(member_request.email)
    secure_password_field_input(member_request.password)
    hashed_password = pwd_context.hash(member_request.password)
    db_member = Member(email=member_request.email, hashed_password=hashed_password)
    db.add(db_member)
    db.commit()
    db.refresh(db_member)
    return {"email": db_member.email}

# Login
@app.post("/login", response_model=LoginResponse)
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    validate_email_format(form_data.username)
    secure_password_field_input(form_data.password)
    db = SessionLocal()
    db_member = db.query(Member).filter(Member.email == form_data.username).first()
    if not db_member:
        raise HTTPException(status_code=400, detail="Incorrect email or password")
    if not db_member.verify_password(form_data.password):
        raise HTTPException(status_code=400, detail="Incorrect email or password")
    access_token = "example_token"
    return {"access_token": access_token, "token_type": "bearer"}