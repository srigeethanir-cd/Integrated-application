# tests/test_component.py

from fastapi.testclient import TestClient
from main import app
from pydantic import BaseModel
from typing import Optional

class Product(BaseModel):
    name: str
    sku: str
    description: Optional[str] = None

client = TestClient(app)

def test_create_product():
    # Test case 1: Product name is mandatory
    response = client.post("/products", json={"sku": "12345"})
    assert response.status_code == 422
    assert response.json()["detail"][0]["msg"] == "field required"

    # Test case 2: SKU must be unique
    client.post("/products", json={"name": "Test Product", "sku": "12345"})
    response = client.post("/products", json={"name": "Test Product 2", "sku": "12345"})
    assert response.status_code == 400
    assert response.json()["detail"] == "SKU must be unique"

    # Test case 3: Product is saved successfully
    response = client.post("/products", json={"name": "Test Product 3", "sku": "67890"})
    assert response.status_code == 201
    assert response.json()["name"] == "Test Product 3"
    assert response.json()["sku"] == "67890"

def test_create_product_with_description():
    response = client.post("/products", json={"name": "Test Product", "sku": "11111", "description": "This is a test product"})
    assert response.status_code == 201
    assert response.json()["name"] == "Test Product"
    assert response.json()["sku"] == "11111"
    assert response.json()["description"] == "This is a test product"

def test_create_product_without_description():
    response = client.post("/products", json={"name": "Test Product", "sku": "22222"})
    assert response.status_code == 201
    assert response.json()["name"] == "Test Product"
    assert response.json()["sku"] == "22222"
    assert "description" not in response.json()