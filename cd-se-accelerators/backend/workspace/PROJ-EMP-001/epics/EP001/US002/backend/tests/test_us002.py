# tests/test_user_registration.py
from fastapi.testclient import TestClient
from main import app
from pydantic import BaseModel
from typing import Optional
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String

# Define the User model
Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    username = Column(String)
    email = Column(String)
    password = Column(String)

# Create a test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL)
Base.metadata.create_all(engine)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Define the User registration request body
class UserRegistrationRequest(BaseModel):
    username: str
    email: str
    password: str

# Define the User registration response
class UserRegistrationResponse(BaseModel):
    id: int
    username: str
    email: str

# Create a test client
client = TestClient(app)

def test_user_registration():
    # Test case 1: Successful user registration
    user_registration_request = {
        "username": "testuser",
        "email": "testuser@example.com",
        "password": "password123"
    }
    response = client.post("/users/", json=user_registration_request)
    assert response.status_code == 201
    assert response.json()["username"] == user_registration_request["username"]
    assert response.json()["email"] == user_registration_request["email"]

    # Test case 2: Duplicate username
    user_registration_request = {
        "username": "testuser",
        "email": "testuser2@example.com",
        "password": "password123"
    }
    response = client.post("/users/", json=user_registration_request)
    assert response.status_code == 400
    assert response.json()["detail"] == "Username already exists"

    # Test case 3: Duplicate email
    user_registration_request = {
        "username": "testuser2",
        "email": "testuser@example.com",
        "password": "password123"
    }
    response = client.post("/users/", json=user_registration_request)
    assert response.status_code == 400
    assert response.json()["detail"] == "Email already exists"

    # Test case 4: Invalid password
    user_registration_request = {
        "username": "testuser3",
        "email": "testuser3@example.com",
        "password": "short"
    }
    response = client.post("/users/", json=user_registration_request)
    assert response.status_code == 400
    assert response.json()["detail"] == "Password must be at least 8 characters long"

def test_user_registration_form_inputs_and_validation_rules():
    # Test case 1: Missing username
    user_registration_request = {
        "email": "testuser@example.com",
        "password": "password123"
    }
    response = client.post("/users/", json=user_registration_request)
    assert response.status_code == 400
    assert response.json()["detail"] == "Username is required"

    # Test case 2: Missing email
    user_registration_request = {
        "username": "testuser",
        "password": "password123"
    }
    response = client.post("/users/", json=user_registration_request)
    assert response.status_code == 400
    assert response.json()["detail"] == "Email is required"

    # Test case 3: Missing password
    user_registration_request = {
        "username": "testuser",
        "email": "testuser@example.com"
    }
    response = client.post("/users/", json=user_registration_request)
    assert response.status_code == 400
    assert response.json()["detail"] == "Password is required"

def test_secure_api_response():
    # Test case 1: Successful user registration with secure API response
    user_registration_request = {
        "username": "testuser",
        "email": "testuser@example.com",
        "password": "password123"
    }
    response = client.post("/users/", json=user_registration_request)
    assert response.status_code == 201
    assert "password" not in response.json()

def test_persist_state_changes_in_database_schema():
    # Test case 1: Successful user registration with persisted state changes
    user_registration_request = {
        "username": "testuser",
        "email": "testuser@example.com",
        "password": "password123"
    }
    response = client.post("/users/", json=user_registration_request)
    assert response.status_code == 201
    db = SessionLocal()
    user = db.query(User).filter(User.username == user_registration_request["username"]).first()
    assert user is not None
    assert user.username == user_registration_request["username"]
    assert