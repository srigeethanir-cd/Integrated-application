from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel, validator
from passlib.context import CryptContext
from jose import jwt, JWTError
from datetime import datetime, timedelta
from typing import Optional

# Initialize FastAPI app
app = FastAPI()

# Define password context
pwd_context = CryptContext(schemes=["bcrypt"], default="bcrypt")

# Define OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

# Define token settings
SECRET_KEY = "secret_key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Define user model
class User(BaseModel):
    id: int
    email: str
    password: str

    @validator("email")
    def validate_email(cls, v):
        if "@" not in v:
            raise ValueError("Invalid email format")
        return v

# Define token model
class Token(BaseModel):
    access_token: str
    token_type: str

# Define token data model
class TokenData(BaseModel):
    email: Optional[str] = None

# Define user database (in-memory for simplicity)
users_db = {}

# Function to verify password
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

# Function to get password hash
def get_password_hash(password):
    return pwd_context.hash(password)

# Function to authenticate user
def authenticate_user(email: str, password: str):
    if email in users_db:
        user = users_db[email]
        if verify_password(password, user.password):
            return user
    return None

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
        token_data = TokenData(email=email)
    except JWTError:
        raise credentials_exception
    user = users_db.get(token_data.email)
    if user is None:
        raise credentials_exception
    return user

# Register user endpoint
@app.post("/register")
async def register_user(email: str, password: str):
    if email in users_db:
        raise HTTPException(status_code=400, detail="Email already registered")
    hashed_password = get_password_hash(password)
    user = User(id=len(users_db) + 1, email=email, password=hashed_password)
    users_db[email] = user
    return {"message": "User registered successfully"}

# Login endpoint
@app.post("/login", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

# Protected endpoint
@app.get("/users/me")
async def read_users_me(current_user: User = Depends(get_current_user)):
    return current_user