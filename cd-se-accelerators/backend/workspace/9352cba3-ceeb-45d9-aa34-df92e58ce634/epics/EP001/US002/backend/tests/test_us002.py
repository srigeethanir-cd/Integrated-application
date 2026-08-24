import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_login_with_credentials():
    response = client.post(
        "/login",
        headers={"Content-Type": "application/json"},
        json={"username": "test_user", "password": "test_password"},
    )
    assert response.status_code == 200
    assert response.json()["message"] == "Login successful"

def test_error_on_invalid_credentials():
    response = client.post(
        "/login",
        headers={"Content-Type": "application/json"},
        json={"username": "invalid_user", "password": "invalid_password"},
    )
    assert response.status_code == 401
    assert response.json()["message"] == "Invalid credentials"

def test_login_with_missing_credentials():
    response = client.post(
        "/login",
        headers={"Content-Type": "application/json"},
        json={"username": "test_user"},
    )
    assert response.status_code == 422
    assert response.json()["message"] == "Missing required fields"

def test_login_with_empty_credentials():
    response = client.post(
        "/login",
        headers={"Content-Type": "application/json"},
        json={},
    )
    assert response.status_code == 422
    assert response.json()["message"] == "Missing required fields"