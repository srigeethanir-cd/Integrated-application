from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from passlib.context import CryptContext
from jose import jwt, JWTError
from datetime import datetime, timedelta

# Initialize FastAPI app
app = FastAPI()

# Initialize database connection
SQLALCHEMY_DATABASE_URL = "sqlite:///user.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Initialize password context
pwd_context = CryptContext(schemes=["bcrypt"], default="bcrypt")

# Initialize OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Define user model
Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)

    def verify_password(self, plain_password):
        return pwd_context.verify(plain_password, self.hashed_password)

# Create database tables
Base.metadata.create_all(bind=engine)

# Define user registration request model
class UserRegistrationRequest(BaseModel):
    username: str
    email: str
    password: str

# Define token response model
class TokenResponse(BaseModel):
    access_token: str
    token_type: str

# Define user registration endpoint
@app.post("/register", response_model=TokenResponse)
async def register_user(user_registration_request: UserRegistrationRequest):
    # Validate user registration request
    if not user_registration_request.username or not user_registration_request.email or not user_registration_request.password:
        raise HTTPException(status_code=400, detail="Invalid user registration request")

    # Check if user already exists
    db = SessionLocal()
    existing_user = db.query(User).filter(User.username == user_registration_request.username).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already taken")

    # Hash user password
    hashed_password = pwd_context.hash(user_registration_request.password)

    # Create new user
    new_user = User(username=user_registration_request.username, email=user_registration_request.email, hashed_password=hashed_password)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # Generate access token
    access_token_expires = timedelta(minutes=30)
    access_token = create_access_token(data={"sub": new_user.username}, expires_delta=access_token_expires)

    # Return token response
    return {"access_token": access_token, "token_type": "bearer"}

# Define function to create access token
def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, "secret_key", algorithm="HS256")
    return encoded_jwt

# Define function to get current user
async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, "secret_key", algorithms=["HS256"])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    db = SessionLocal()
    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise credentials_exception
    return user