import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_user_login_valid_credentials():
    # Arrange
    user_data = {
        "email": "test@example.com",
        "password": "password123"
    }
    # Act
    response = client.post("/login", json=user_data)
    # Assert
    assert response.status_code == 200
    assert response.json()["message"] == "Login successful"

def test_user_login_invalid_credentials():
    # Arrange
    user_data = {
        "email": "test@example.com",
        "password": "wrongpassword"
    }
    # Act
    response = client.post("/login", json=user_data)
    # Assert
    assert response.status_code == 401
    assert response.json()["message"] == "Invalid email or password"

def test_user_login_empty_credentials():
    # Arrange
    user_data = {
        "email": "",
        "password": ""
    }
    # Act
    response = client.post("/login", json=user_data)
    # Assert
    assert response.status_code == 400
    assert response.json()["message"] == "Email and password are required"

def test_user_login_missing_credentials():
    # Arrange
    user_data = {
        "email": "test@example.com"
    }
    # Act
    response = client.post("/login", json=user_data)
    # Assert
    assert response.status_code == 400
    assert response.json()["message"] == "Email and password are required"