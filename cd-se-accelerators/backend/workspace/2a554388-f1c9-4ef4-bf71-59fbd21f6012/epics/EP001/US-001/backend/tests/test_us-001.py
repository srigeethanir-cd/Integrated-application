# tests/test_component.py

from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_create_component():
    response = client.post(
        "/component/",
        json={"name": "Test Component", "description": "This is a test component"},
    )
    assert response.status_code == 201
    assert response.json()["name"] == "Test Component"
    assert response.json()["description"] == "This is a test component"

def test_create_component_invalid_json():
    response = client.post("/component/", json={"invalid": "json"})
    assert response.status_code == 422

def test_create_component_missing_required_fields():
    response = client.post("/component/", json={})
    assert response.status_code == 422

def test_create_component_duplicate_name():
    # Create a component with a unique name
    client.post(
        "/component/",
        json={"name": "Unique Component", "description": "This is a unique component"},
    )
    
    # Try to create another component with the same name
    response = client.post(
        "/component/",
        json={"name": "Unique Component", "description": "This is another unique component"},
    )
    assert response.status_code == 400