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
    assert response.status_code == 200
    assert response.url == "http://testserver/login"

    # Validate session invalidation
    response = client.get("/protected", cookies=cookies)
    assert response.status_code == 401

def test_logout_redirects_to_login_page():
    # Arrange
    login_data = {"username": "test_user", "password": "test_password"}
    response = client.post("/login", data=login_data)
    assert response.status_code == 200
    cookies = response.cookies

    # Act
    response = client.post("/logout", cookies=cookies)

    # Assert
    assert response.status_code == 200
    assert response.url == "http://testserver/login"