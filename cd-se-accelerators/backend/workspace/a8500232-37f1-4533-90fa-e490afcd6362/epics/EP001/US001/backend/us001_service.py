from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from typing import Optional
from passlib.context import CryptContext
from datetime import datetime, timedelta
from jose import jwt, JWTError

# Define the FastAPI application
app = FastAPI()

# Define the user model
class User(BaseModel):
    id: Optional[int]
    name: str
    email: str
    password: str

# Define the user database (in-memory for simplicity)
users_db = {}

# Define the password context
pwd_context = CryptContext(schemes=["bcrypt"], default="bcrypt")

# Define the OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Define the secret key for JWT
SECRET_KEY = "secret_key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Function to verify password
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

# Function to get password hash
def get_password_hash(password):
    return pwd_context.hash(password)

# Function to create access token
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# Function to get current user
async def get_current_user(token: str = Depends(oauth2_scheme)):
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
    user = users_db.get(email)
    if user is None:
        raise credentials_exception
    return user

# Register user endpoint
@app.post("/register")
async def register_user(user: User):
    if users_db.get(user.email):
        raise HTTPException(status_code=400, detail="Email already registered")
    hashed_password = get_password_hash(user.password)
    users_db[user.email] = {
        "id": len(users_db) + 1,
        "name": user.name,
        "email": user.email,
        "password": hashed_password,
    }
    return {"message": "User registered successfully"}

# Login user endpoint
@app.post("/token")
async def login_user(form_data: OAuth2PasswordRequestForm = Depends()):
    user = users_db.get(form_data.username)
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not verify_password(form_data.password, user["password"]):
        raise HTTPException(
            status_code=401,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user["email"]}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

# Protected route
@app.get("/users/me")
async def read_users_me(current_user: User = Depends(get_current_user)):
    return current_user