# tests/test_user_login.py

from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_user_login_success():
    # Arrange
    email = "test@example.com"
    password = "password123"

    # Act
    response = client.post(
        "/login",
        headers={"Content-Type": "application/json"},
        json={"email": email, "password": password},
    )

    # Assert
    assert response.status_code == 200
    assert response.json()["token"] is not None

def test_user_login_invalid_email():
    # Arrange
    email = "invalid-email"
    password = "password123"

    # Act
    response = client.post(
        "/login",
        headers={"Content-Type": "application/json"},
        json={"email": email, "password": password},
    )

    # Assert
    assert response.status_code == 401
    assert response.json()["error"] == "Invalid email or password"

def test_user_login_invalid_password():
    # Arrange
    email = "test@example.com"
    password = "invalid-password"

    # Act
    response = client.post(
        "/login",
        headers={"Content-Type": "application/json"},
        json={"email": email, "password": password},
    )

    # Assert
    assert response.status_code == 401
    assert response.json()["error"] == "Invalid email or password"

def test_user_login_missing_email():
    # Arrange
    password = "password123"

    # Act
    response = client.post(
        "/login",
        headers={"Content-Type": "application/json"},
        json={"password": password},
    )

    # Assert
    assert response.status_code == 422
    assert response.json()["error"] == "Email is required"

def test_user_login_missing_password():
    # Arrange
    email = "test@example.com"

    # Act
    response = client.post(
        "/login",
        headers={"Content-Type": "application/json"},
        json={"email": email},
    )

    # Assert
    assert response.status_code == 422
    assert response.json()["error"] == "Password is required"