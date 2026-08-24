# tests/test_component.py

from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_create_component():
    """
    Test creating a new component
    """
    response = client.post(
        "/component/",
        json={"name": "Test Component", "description": "This is a test component"},
    )
    assert response.status_code == 201
    assert response.json()["name"] == "Test Component"
    assert response.json()["description"] == "This is a test component"

def test_create_component_invalid_json():
    """
    Test creating a new component with invalid JSON
    """
    response = client.post("/component/", json={"invalid": "json"})
    assert response.status_code == 422

def test_create_component_missing_fields():
    """
    Test creating a new component with missing fields
    """
    response = client.post("/component/", json={"name": "Test Component"})
    assert response.status_code == 422

def test_create_component_duplicate():
    """
    Test creating a duplicate component
    """
    client.post(
        "/component/",
        json={"name": "Test Component", "description": "This is a test component"},
    )
    response = client.post(
        "/component/",
        json={"name": "Test Component", "description": "This is a test component"},
    )
    assert response.status_code == 400