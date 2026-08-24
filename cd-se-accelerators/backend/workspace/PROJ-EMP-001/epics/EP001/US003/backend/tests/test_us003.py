# tests/test_component.py

from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_create_component():
    # Arrange
    component_data = {
        "name": "Test Component",
        "description": "This is a test component"
    }

    # Act
    response = client.post("/components/", json=component_data)

    # Assert
    assert response.status_code == 201
    assert response.json()["name"] == component_data["name"]
    assert response.json()["description"] == component_data["description"]

def test_create_component_invalid_data():
    # Arrange
    component_data = {
        "name": None,
        "description": "This is a test component"
    }

    # Act
    response = client.post("/components/", json=component_data)

    # Assert
    assert response.status_code == 422

def test_create_component_duplicate():
    # Arrange
    component_data = {
        "name": "Test Component",
        "description": "This is a test component"
    }
    client.post("/components/", json=component_data)

    # Act
    response = client.post("/components/", json=component_data)

    # Assert
    assert response.status_code == 400