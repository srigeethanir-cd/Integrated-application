from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from passlib.context import CryptContext
from datetime import datetime, timedelta
from jose import jwt, JWTError

# Define the FastAPI application
app = FastAPI()

# Define the secret key for JWT
SECRET_KEY = "your-secret-key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Define the password context
pwd_context = CryptContext(schemes=["bcrypt"], default="bcrypt")

# Define the user model
class User(BaseModel):
    id: int
    email: str
    password: str

# Define the token model
class Token(BaseModel):
    access_token: str
    token_type: str

# Define the token data model
class TokenData(BaseModel):
    email: str | None = None

# Define the OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

# Define the function to verify password
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

# Define the function to get password hash
def get_password_hash(password):
    return pwd_context.hash(password)

# Define the function to authenticate user
def authenticate_user(email: str, password: str):
    # Replace this with your actual database query
    user = None
    for u in users:
        if u.email == email:
            user = u
            break
    if not user:
        return False
    if not verify_password(password, user.password):
        return False
    return user

# Define the function to create access token
def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# Define the function to get current user
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
    # Replace this with your actual database query
    user = None
    for u in users:
        if u.email == token_data.email:
            user = u
            break
    if user is None:
        raise credentials_exception
    return user

# Define the users list (replace with your actual database)
users = [
    User(id=1, email="user1@example.com", password=get_password_hash("password1")),
    User(id=2, email="user2@example.com", password=get_password_hash("password2")),
]

# Define the login endpoint
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
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

# Define the protected endpoint
@app.get("/users/me")
async def read_users_me(current_user: User = Depends(get_current_user)):
    return current_user