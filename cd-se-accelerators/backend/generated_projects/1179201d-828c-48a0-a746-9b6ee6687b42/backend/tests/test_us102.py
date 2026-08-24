# tests/test_member_registration.py

from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_member_registration_password_confirmation_match():
    # Given
    username = "test_user"
    email = "test@example.com"
    password = "password123"
    password_confirmation = "password123"

    # When
    response = client.post(
        "/register",
        json={
            "username": username,
            "email": email,
            "password": password,
            "password_confirmation": password_confirmation,
        },
    )

    # Then
    assert response.status_code == 201
    assert response.json()["message"] == "Member registered successfully"

def test_member_registration_password_confirmation_mismatch():
    # Given
    username = "test_user"
    email = "test@example.com"
    password = "password123"
    password_confirmation = "wrong_password"

    # When
    response = client.post(
        "/register",
        json={
            "username": username,
            "email": email,
            "password": password,
            "password_confirmation": password_confirmation,
        },
    )

    # Then
    assert response.status_code == 400
    assert response.json()["message"] == "Password confirmation does not match"