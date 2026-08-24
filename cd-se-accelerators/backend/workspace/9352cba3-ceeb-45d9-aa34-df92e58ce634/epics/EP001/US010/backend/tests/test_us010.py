# tests/test_logout.py
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_logout():
    # Arrange
    login_data = {"username": "test_user", "password": "test_password"}
    response = client.post("/login", data=login_data)
    assert response.status_code == 200
    cookies = response.cookies

    # Act
    response = client.post("/logout", cookies=cookies)

    # Assert
    assert response.status_code == 302
    assert response.headers["location"] == "/login"

    # Verify session is invalidated
    response = client.get("/protected", cookies=cookies)
    assert response.status_code == 401

def test_logout_without_session():
    # Act
    response = client.post("/logout")

    # Assert
    assert response.status_code == 302
    assert response.headers["location"] == "/login"