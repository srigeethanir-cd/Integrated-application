# tests/test_user_login.py

from fastapi.testclient import TestClient
from main import app
from pydantic import BaseModel
from typing import Dict

class User(BaseModel):
    email: str
    password: str

def test_user_login_success():
    client = TestClient(app)
    user_data = {
        "email": "test@example.com",
        "password": "password123"
    }
    response = client.post("/login", json=user_data)
    assert response.status_code == 200
    assert response.json()["token"] is not None

def test_user_login_failure_invalid_email():
    client = TestClient(app)
    user_data = {
        "email": "invalid_email",
        "password": "password123"
    }
    response = client.post("/login", json=user_data)
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid email or password"

def test_user_login_failure_invalid_password():
    client = TestClient(app)
    user_data = {
        "email": "test@example.com",
        "password": "invalid_password"
    }
    response = client.post("/login", json=user_data)
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid email or password"

def test_user_login_failure_missing_email():
    client = TestClient(app)
    user_data = {
        "password": "password123"
    }
    response = client.post("/login", json=user_data)
    assert response.status_code == 422
    assert response.json()["detail"][0]["msg"] == "field required"

def test_user_login_failure_missing_password():
    client = TestClient(app)
    user_data = {
        "email": "test@example.com"
    }
    response = client.post("/login", json=user_data)
    assert response.status_code == 422
    assert response.json()["detail"][0]["msg"] == "field required"