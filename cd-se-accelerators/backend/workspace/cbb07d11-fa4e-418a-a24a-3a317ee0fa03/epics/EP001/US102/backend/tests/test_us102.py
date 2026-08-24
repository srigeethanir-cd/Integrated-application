# tests/test_member_registration.py

from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_member_registration_password_confirmation_match():
    # Given
    registration_data = {
        "username": "test_user",
        "email": "test@example.com",
        "password": "test_password",
        "password_confirmation": "test_password"
    }

    # When
    response = client.post("/register", json=registration_data)

    # Then
    assert response.status_code == 201
    assert response.json()["message"] == "Member registered successfully"

def test_member_registration_password_confirmation_mismatch():
    # Given
    registration_data = {
        "username": "test_user",
        "email": "test@example.com",
        "password": "test_password",
        "password_confirmation": "mismatched_password"
    }

    # When
    response = client.post("/register", json=registration_data)

    # Then
    assert response.status_code == 400
    assert response.json()["message"] == "Password confirmation does not match"