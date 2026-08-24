import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_register_user():
    # Test data
    user_data = {
        "name": "John Doe",
        "email": "johndoe@example.com",
        "password": "password123"
    }

    # Send POST request to register user
    response = client.post("/register", json=user_data)

    # Assert response status code
    assert response.status_code == 201

    # Assert response JSON
    assert response.json() == {"message": "User registered successfully"}

def test_register_user_with_duplicate_email():
    # Test data
    user_data = {
        "name": "John Doe",
        "email": "johndoe@example.com",
        "password": "password123"
    }

    # Send POST request to register user
    client.post("/register", json=user_data)

    # Send another POST request to register user with same email
    response = client.post("/register", json=user_data)

    # Assert response status code
    assert response.status_code == 400

    # Assert response JSON
    assert response.json() == {"error": "Email already exists"}

def test_register_user_with_invalid_data():
    # Test data
    user_data = {
        "name": "",
        "email": "invalid_email",
        "password": ""
    }

    # Send POST request to register user
    response = client.post("/register", json=user_data)

    # Assert response status code
    assert response.status_code == 422

    # Assert response JSON
    assert response.json()["detail"][0]["msg"] == "value is not a valid email"