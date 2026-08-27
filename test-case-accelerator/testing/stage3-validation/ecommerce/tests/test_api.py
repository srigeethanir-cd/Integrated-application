from fastapi.testclient import TestClient
from uuid import uuid4
from main import app
client = TestClient(app)
def test_product_validation():
    assert client.post("/api/v1/store/products", json={"sku": "bad", "name": "X", "price": 0, "stock": -1}).status_code == 422
def test_product_creation():
    sku = f"SKU-{uuid4().hex[:8].upper()}"
    response = client.post("/api/v1/store/products", json={"sku": sku, "name": "Keyboard", "price": "50", "stock": 4})
    assert response.status_code == 201
