# tests/test_auth_portal.py

from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_email_format_validation():
    # Test with valid email
    response = client.post(
        "/auth/portal",
        json={"email": "test@example.com", "password": "password123"}
    )
    assert response.status_code == 200

    # Test with invalid email
    response = client.post(
        "/auth/portal",
        json={"email": "invalid_email", "password": "password123"}
    )
    assert response.status_code == 422

    # Test with missing email
    response = client.post(
        "/auth/portal",
        json={"password": "password123"}
    )
    assert response.status_code == 422

def test_email_format_validation_edge_cases():
    # Test with email containing special characters
    response = client.post(
        "/auth/portal",
        json={"email": "test+special@example.com", "password": "password123"}
    )
    assert response.status_code == 200

    # Test with email containing numbers
    response = client.post(
        "/auth/portal",
        json={"email": "test123@example.com", "password": "password123"}
    )
    assert response.status_code == 200

    # Test with email containing underscores
    response = client.post(
        "/auth/portal",
        json={"email": "test_underscore@example.com", "password": "password123"}
    )
    assert response.status_code == 200

def test_email_format_validation_error_messages():
    # Test with invalid email
    response = client.post(
        "/auth/portal",
        json={"email": "invalid_email", "password": "password123"}
    )
    assert response.json()["detail"][0]["msg"] == "value is not a valid email address"

    # Test with missing email
    response = client.post(
        "/auth/portal",
        json={"password": "password123"}
    )
    assert response.json()["detail"][0]["msg"] == "field required"