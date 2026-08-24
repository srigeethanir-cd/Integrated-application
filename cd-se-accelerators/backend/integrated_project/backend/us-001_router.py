from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from passlib.context import CryptContext
from datetime import datetime, timedelta
from jose import jwt, JWTError

# Define the FastAPI application
app = FastAPI()

# Define the user model
class User(BaseModel):
    email: str
    password: str

# Define the token model
class Token(BaseModel):
    access_token: str
    token_type: str

# Define the token data model
class TokenData(BaseModel):
    email: str | None = None

# Define the password context
pwd_context = CryptContext(schemes=["bcrypt"], default="bcrypt")

# Define the secret key and algorithm for JWT
SECRET_KEY = "secret_key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Define the OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

# Function to verify password
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

# Function to get password hash
def get_password_hash(password):
    return pwd_context.hash(password)

# Function to authenticate user
def authenticate_user(email: str, password: str):
    # Replace this with your actual user database
    users = {
        "user@example.com": get_password_hash("password"),
    }
    if email in users:
        if verify_password(password, users[email]):
            return email
    return None

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
    # Replace this with your actual user database
    users = {
        "user@example.com": get_password_hash("password"),
    }
    if email not in users:
        raise credentials_exception
    return email

# Login endpoint
@app.post("/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

# Protected endpoint
@app.get("/users/me")
async def read_users_me(current_user: str = Depends(get_current_user)):
    return {"email": current_user}