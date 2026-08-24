python
# database.py
from sqlalchemy import create_engine, Column, String, Integer
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError
from pydantic import BaseModel
from passlib.context import CryptContext
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from fastapi.requests import Request

# Initialize FastAPI app
app = FastAPI()

# Initialize database connection
SQLALCHEMY_DATABASE_URL = "sqlite:///database.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Initialize password hashing
pwd_context = CryptContext(schemes=["bcrypt"], default="bcrypt")

# Define database model
Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    password = Column(String)

# Create database tables
Base.metadata.create_all(bind=engine)

# Define request and response models
class UserRegistrationRequest(BaseModel):
    email: str
    password: str

class UserRegistrationResponse(BaseModel):
    email: str
    id: int

# Define email validation function
def validate_email(email: str):
    if "@" not in email:
        raise ValueError("Invalid email address")
    return email

# Define password hashing function
def hash_password(password: str):
    return pwd_context.hash(password)

# Define user registration function
def register_user(db, user_request: UserRegistrationRequest):
    try:
        # Validate email
        validate_email(user_request.email)
        
        # Hash password
        hashed_password = hash_password(user_request.password)
        
        # Create new user
        new_user = User(email=user_request.email, password=hashed_password)
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        
        # Return user registration response
        return UserRegistrationResponse(email=new_user.email, id=new_user.id)
    except IntegrityError:
        raise HTTPException(status_code=400, detail="Email already registered")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Define user registration endpoint
@app.post("/register", response_model=UserRegistrationResponse)
async def register_user_endpoint(user_request: UserRegistrationRequest):
    db = SessionLocal()
    try:
        return register_user(db, user_request)
    finally:
        db.close()

# Define React TypeScript interface for user registration request
class UserRegistrationRequestInterface {
    email: string;
    password: string;
}

# Define React TypeScript interface for user registration response
class UserRegistrationResponseInterface {
    email: string;
    id: number;
}

# Example usage
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)