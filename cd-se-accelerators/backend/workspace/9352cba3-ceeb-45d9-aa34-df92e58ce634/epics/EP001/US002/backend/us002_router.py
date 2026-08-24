from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from passlib.context import CryptContext
from datetime import datetime, timedelta
from jose import jwt

app = FastAPI()

# Define the user model
class User(BaseModel):
    username: str
    password: str

# Define the token model
class Token(BaseModel):
    access_token: str
    token_type: str

# Define the token data model
class TokenData(BaseModel):
    username: str | None = None

# Define the password context
pwd_context = CryptContext(schemes=["bcrypt"], default="bcrypt")

# Define the secret key and algorithm for JWT
SECRET_KEY = "your_secret_key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Define the OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

# Define the user database (replace with a real database)
users_db = {
    "user1": {
        "username": "user1",
        "password": pwd_context.hash("password1")
    },
    "user2": {
        "username": "user2",
        "password": pwd_context.hash("password2")
    }
}

# Function to verify password
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

# Function to get password hash
def get_password_hash(password):
    return pwd_context.hash(password)

# Function to authenticate user
def authenticate_user(username: str, password: str):
    user = users_db.get(username)
    if not user:
        return False
    if not verify_password(password, user["password"]):
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

# Login endpoint
@app.post("/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user["username"]}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

# Protected endpoint
@app.get("/dashboard")
async def dashboard(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(
                status_code=401, detail="Invalid token"
            )
        return {"message": f"Welcome, {username}!"}
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=401, detail="Token has expired"
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=401, detail="Invalid token"
        )