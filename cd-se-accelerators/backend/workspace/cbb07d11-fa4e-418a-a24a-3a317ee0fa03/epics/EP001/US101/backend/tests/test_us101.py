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
    # Test password length
    assert len(password) >= 8
    # Test password contains at least one uppercase letter
    assert any(char.isupper() for char in password)
    # Test password contains at least one lowercase letter
    assert any(char.islower() for char in password)
    # Test password contains at least one digit
    assert any(char.isdigit() for char in password)

def test_member_login():
    """Test member login"""
    # Test valid login credentials
    valid_email = "test@example.com"
    valid_password = "password123"
    response = client.post("/login", json={"email": valid_email, "password": valid_password})
    assert response.status_code == 200
    # Test invalid login credentials
    invalid_email = "invalid_email"
    invalid_password = "invalid_password"
    response = client.post("/login", json={"email": invalid_email, "password": invalid_password})
    assert response.status_code == 401

def test_member_login_email_validation():
    """Test member login email validation"""
    # Test valid email format
    valid_email = "test@example.com"
    response = client.post("/login", json={"email": valid_email, "password": "password123"})
    assert response.status_code == 200
    # Test invalid email format
    invalid_email = "invalid_email"
    response = client.post("/login", json={"email": invalid_email, "password": "password123"})
    assert response.status_code == 400

def test_member_login_password_validation():
    """Test member login password validation"""
    # Test valid password
    valid_password = "password123"
    response = client.post("/login", json={"email": "test@example.com", "password": valid_password})
    assert response.status_code == 200
    # Test invalid password
    invalid_password = "invalid"
    response = client.post("/login", json={"email": "test@example.com", "password": invalid_password})
    assert response.status_code == 400