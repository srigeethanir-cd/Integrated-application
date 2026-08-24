# tests/test_user_login.py
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_user_login():
    # Test login with valid credentials
    response = client.post(
        "/login",
        headers={"Content-Type": "application/json"},
        json={"username": "test_user", "password": "test_password"},
    )
    assert response.status_code == 200
    assert response.json()["message"] == "Login successful"

def test_user_login_invalid_credentials():
    # Test login with invalid credentials
    response = client.post(
        "/login",
        headers={"Content-Type": "application/json"},
        json={"username": "invalid_user", "password": "invalid_password"},
    )
    assert response.status_code == 401
    assert response.json()["message"] == "Invalid credentials"

def test_user_login_missing_credentials():
    # Test login with missing credentials
    response = client.post(
        "/login",
        headers={"Content-Type": "application/json"},
        json={},
    )
    assert response.status_code == 422
    assert response.json()["message"] == "Missing required fields: username, password"

def test_user_login_empty_credentials():
    # Test login with empty credentials
    response = client.post(
        "/login",
        headers={"Content-Type": "application/json"},
        json={"username": "", "password": ""},
    )
    assert response.status_code == 422
    assert response.json()["message"] == "Invalid credentials"