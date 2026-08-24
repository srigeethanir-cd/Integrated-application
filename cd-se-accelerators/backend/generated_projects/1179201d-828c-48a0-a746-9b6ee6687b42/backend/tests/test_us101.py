# tests/test_member_login.py
from fastapi.testclient import TestClient
from main import app
import pytest
from pydantic import ValidationError
from typing import Dict

client = TestClient(app)

def test_validate_email_format():
    """
    Test to validate email format
    """
    # Valid email
    valid_email = "test@example.com"
    response = client.post("/login", json={"email": valid_email, "password": "password123"})
    assert response.status_code == 200

    # Invalid email
    invalid_email = "invalid_email"
    response = client.post("/login", json={"email": invalid_email, "password": "password123"})
    assert response.status_code == 422

def test_secure_password_field_input():
    """
    Test to secure password field input
    """
    # Valid password
    valid_password = "password123"
    response = client.post("/login", json={"email": "test@example.com", "password": valid_password})
    assert response.status_code == 200

    # Invalid password (less than 8 characters)
    invalid_password = "pass"
    response = client.post("/login", json={"email": "test@example.com", "password": invalid_password})
    assert response.status_code == 422

    # Invalid password (no uppercase letter)
    invalid_password = "password123"
    response = client.post("/login", json={"email": "test@example.com", "password": invalid_password})
    assert response.status_code == 422

def test_login_endpoint():
    """
    Test to check login endpoint
    """
    # Valid credentials
    valid_credentials: Dict[str, str] = {"email": "test@example.com", "password": "Password123"}
    response = client.post("/login", json=valid_credentials)
    assert response.status_code == 200

    # Invalid credentials
    invalid_credentials: Dict[str, str] = {"email": "test@example.com", "password": "wrong_password"}
    response = client.post("/login", json=invalid_credentials)
    assert response.status_code == 401