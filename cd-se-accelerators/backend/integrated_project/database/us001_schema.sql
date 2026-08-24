python
# models.py
from sqlalchemy import Column, String, Integer
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    email = Column(String, unique=True)
    password = Column(String)

    def __repr__(self):
        return f"User(id={self.id}, email='{self.email}', password='{self.password}')"

# database.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base

SQLALCHEMY_DATABASE_URL = "sqlite:///database.db"

engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# schemas.py
from pydantic import BaseModel
from typing import Optional

class UserCreate(BaseModel):
    email: str
    password: str

class UserLogin(BaseModel):
    email: str
    password: str

class UserResponse(BaseModel):
    id: int
    email: str

    class Config:
        orm_mode = True

# crud.py
from models import User
from schemas import UserCreate, UserLogin
from database import get_db
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi import Depends, HTTPException
from jose import jwt
from datetime import datetime, timedelta
from typing import Optional

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

def get_user(db: Session, email: str):
    return db.query(User).filter(User.email == email).first()

def create_user(db: Session, user: UserCreate):
    db_user = User(email=user.email, password=user.password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def authenticate_user(db: Session, email: str, password: str):
    user = get_user(db, email)
    if not user:
        return False
    if user.password != password:
        return False
    return user

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, "secret_key", algorithm="HS256")
    return encoded_jwt

def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, "secret_key", algorithms=["HS256"])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=401,
            detail="Access token expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.JWTClaimsError:
        raise HTTPException(
            status_code=401,
            detail="Invalid claims",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.JWTError:
        raise HTTPException(
            status_code=401,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    db = next(get_db())
    user = get_user(db, email)
    if user is None:
        raise credentials_exception
    return user

# main.py
from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from crud import create_user, authenticate_user, create_access_token, get_current_user
from schemas import UserCreate, UserLogin, UserResponse
from database import get_db

app = FastAPI()

@app.post("/register")
async def create_new_user(user: UserCreate):
    db = next(get_db())
    db_user = create_user(db, user)
    return {"email": db_user.email}

@app.post("/login")
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    db = next(get_db())
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=30)
    access_token = create_access_token(
        data={"sub": user.email},