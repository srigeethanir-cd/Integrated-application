# tests/test_member_registration.py

from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_validate_password_confirmation_match():
    # Test case 1: Password and confirmation match
    response = client.post(
        "/register",
        json={
            "username": "testuser",
            "email": "test@example.com",
            "password": "password123",
            "password_confirmation": "password123"
        }
    )
    assert response.status_code == 201

    # Test case 2: Password and confirmation do not match
    response = client.post(
        "/register",
        json={
            "username": "testuser",
            "email": "test@example.com",
            "password": "password123",
            "password_confirmation": "differentpassword"
        }
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Password and confirmation do not match"

    # Test case 3: Password confirmation is missing
    response = client.post(
        "/register",
        json={
            "username": "testuser",
            "email": "test@example.com",
            "password": "password123"
        }
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Password confirmation is required"

    # Test case 4: Password is missing
    response = client.post(
        "/register",
        json={
            "username": "testuser",
            "email": "test@example.com",
            "password_confirmation": "password123"
        }
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Password is required"