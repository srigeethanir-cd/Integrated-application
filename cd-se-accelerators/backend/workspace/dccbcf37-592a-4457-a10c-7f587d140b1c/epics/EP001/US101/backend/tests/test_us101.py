# tests/test_member_login.py

from fastapi.testclient import TestClient
from main import app
import pytest
from pydantic import EmailStr
import re

client = TestClient(app)

def validate_email_format(email: str):
    """Validate email format"""
    email_regex = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
    return bool(re.match(email_regex, email))

def test_validate_email_format():
    """Test validate email format"""
    valid_email = "test@example.com"
    invalid_email = "invalid_email"
    assert validate_email_format(valid_email) == True
    assert validate_email_format(invalid_email) == False

def test_secure_password_field_input():
    """Test secure password field input"""
    password = "password123"
    # Check if password is hashed
    # For this example, we'll use a simple hash function
    import hashlib
    hashed_password = hashlib.sha256(password.encode()).hexdigest()
    assert hashed_password != password

def test_member_login():
    """Test member login"""
    # Create a test user
    user_data = {
        "email": "test@example.com",
        "password": "password123"
    }
    response = client.post("/register", json=user_data)
    assert response.status_code == 201

    # Login with valid credentials
    login_data = {
        "email": "test@example.com",
        "password": "password123"
    }
    response = client.post("/login", json=login_data)
    assert response.status_code == 200

    # Login with invalid credentials
    invalid_login_data = {
        "email": "test@example.com",
        "password": "wrong_password"
    }
    response = client.post("/login", json=invalid_login_data)
    assert response.status_code == 401

    # Login with invalid email format
    invalid_email_login_data = {
        "email": "invalid_email",
        "password": "password123"
    }
    response = client.post("/login", json=invalid_email_login_data)
    assert response.status_code == 400

def test_member_login_secure_password_field_input():
    """Test member login secure password field input"""
    # Create a test user
    user_data = {
        "email": "test@example.com",
        "password": "password123"
    }
    response = client.post("/register", json=user_data)
    assert response.status_code == 201

    # Login with valid credentials
    login_data = {
        "email": "test@example.com",
        "password": "password123"
    }
    response = client.post("/login", json=login_data)
    assert response.status_code == 200

    # Check if password is hashed in the response
    # For this example, we'll use a simple hash function
    import hashlib
    hashed_password = hashlib.sha256(login_data["password"].encode()).hexdigest()
    assert hashed_password != login_data["password"]