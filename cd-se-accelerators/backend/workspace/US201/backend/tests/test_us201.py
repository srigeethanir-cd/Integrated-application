# tests/test_user_registration.py
from fastapi.testclient import TestClient
from main import app
from pydantic import EmailStr
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database import Base, get_db
from models import User
from utils import get_password_hash

# Create a test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(SQLALCHEMY_DATABASE_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)

def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

def test_user_registration():
    # Test email validation
    response = client.post(
        "/users/",
        json={"email": "invalid_email", "password": "password123"},
    )
    assert response.status_code == 422

    # Test password hashing
    response = client.post(
        "/users/",
        json={"email": "user@example.com", "password": "password123"},
    )
    assert response.status_code == 201
    user_id = response.json()["id"]

    db = next(override_get_db())
    user = db.query(User).filter(User.id == user_id).first()
    assert user.hashed_password != "password123"
    assert get_password_hash("password123") == user.hashed_password

def test_user_registration_duplicate_email():
    # Test duplicate email
    response = client.post(
        "/users/",
        json={"email": "user@example.com", "password": "password123"},
    )
    assert response.status_code == 201

    response = client.post(
        "/users/",
        json={"email": "user@example.com", "password": "password123"},
    )
    assert response.status_code == 400

def test_user_registration_invalid_password():
    # Test invalid password
    response = client.post(
        "/users/",
        json={"email": "user@example.com", "password": "short"},
    )
    assert response.status_code == 422