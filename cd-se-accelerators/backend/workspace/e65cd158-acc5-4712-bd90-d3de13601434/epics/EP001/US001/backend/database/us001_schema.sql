python
# database.py
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from pydantic import BaseModel
from fastapi import Depends, FastAPI, HTTPException
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import jwt, JWTError
from datetime import datetime, timedelta
from typing import Optional

# Database Configuration
SQLALCHEMY_DATABASE_URL = "sqlite:///database.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# User Model
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    password = Column(String)

Base.metadata.create_all(bind=engine)

# Pydantic User Model
class UserPydantic(BaseModel):
    email: str
    password: str

# OAuth2 Configuration
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

# FastAPI App
app = FastAPI()

# Token Configuration
SECRET_KEY = "secret_key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Generate Token
def generate_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# Verify Token
def verify_token(token: str):
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    return email

# Get Current User
async def get_current_user(token: str = Depends(oauth2_scheme)):
    email = verify_token(token)
    db = SessionLocal()
    user = db.query(User).filter(User.email == email).first()
    if user is None:
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user

# Login
@app.post("/login")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    db = SessionLocal()
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if user.password != form_data.password:
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = generate_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

# Register
@app.post("/register")
async def register(user: UserPydantic):
    db = SessionLocal()
    new_user = User(email=user.email, password=user.password)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

# Protected Route
@app.get("/users/me")
async def read_users_me(current_user: User = Depends(get_current_user)):
    return current_user