from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr
from passlib.context import CryptContext
from jose import jwt, JWTError
from datetime import datetime, timedelta

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
    email: EmailStr
    password: str

# Define token model
class Token(BaseModel):
    access_token: str
    token_type: str

# Define token data model
class TokenData(BaseModel):
    email: EmailStr | None = None

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
    if email not in users_db:
        return False
    user = users_db[email]
    if not verify_password(password, user.hashed_password):
        return False
    return user

# Function to create access token
def create_access_token(data: dict, expires_delta: timedelta | None = None):
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

# Function to validate email format
def validate_email_format(email: str):
    if not email:
        return False
    if "@" not in email:
        return False
    return True

# Function to secure password field input
def secure_password_field_input(password: str):
    if not password:
        return False
    if len(password) < 8:
        return False
    return True

# Register user
@app.post("/register")
async def register_user(email: str, password: str):
    if not validate_email_format(email):
        raise HTTPException(status_code=400, detail="Invalid email format")
    if not secure_password_field_input(password):
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters long")
    hashed_password = get_password_hash(password)
    user = User(id=len(users_db) + 1, email=email, password=hashed_password)
    users_db[email] = user
    return {"message": "User registered successfully"}

# Login user
@app.post("/login", response_model=Token)
async def login_user(form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

# Get current user
@app.get("/users/me")
async def read_users_me(current_user: User = Depends(get_current_user)):
    return current_user