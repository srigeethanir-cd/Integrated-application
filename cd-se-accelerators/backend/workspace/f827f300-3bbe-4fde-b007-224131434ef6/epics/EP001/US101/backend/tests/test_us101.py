# tests/test_member_login.py

from fastapi.testclient import TestClient
from main import app
import pytest
from pydantic import ValidationError
from member_login import MemberLogin

client = TestClient(app)

def test_validate_email_format():
    # Test valid email format
    valid_email = "test@example.com"
    member_login = MemberLogin(email=valid_email, password="password123")
    assert member_login.email == valid_email

    # Test invalid email format
    invalid_email = "invalid_email"
    with pytest.raises(ValidationError):
        MemberLogin(email=invalid_email, password="password123")

def test_secure_password_field_input():
    # Test password length
    short_password = "pass"
    with pytest.raises(ValidationError):
        MemberLogin(email="test@example.com", password=short_password)

    # Test password complexity
    weak_password = "password"
    with pytest.raises(ValidationError):
        MemberLogin(email="test@example.com", password=weak_password)

    # Test valid password
    valid_password = "Password123!"
    member_login = MemberLogin(email="test@example.com", password=valid_password)
    assert member_login.password == valid_password

def test_member_login_api():
    # Test successful login
    valid_email = "test@example.com"
    valid_password = "Password123!"
    response = client.post("/login", json={"email": valid_email, "password": valid_password})
    assert response.status_code == 200

    # Test invalid email
    invalid_email = "invalid_email"
    response = client.post("/login", json={"email": invalid_email, "password": valid_password})
    assert response.status_code == 400

    # Test invalid password
    invalid_password = "wrong_password"
    response = client.post("/login", json={"email": valid_email, "password": invalid_password})
    assert response.status_code == 400