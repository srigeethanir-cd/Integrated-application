from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_authentication_is_required():
    assert client.get("/api/banking/accounts").status_code == 422

def test_open_account():
    response = client.post("/api/banking/accounts", headers={"x-api-key": "validation-bank-key"}, json={"owner": "Ada", "opening_balance": "100.00"})
    assert response.status_code == 201
    assert response.json()["owner"] == "Ada"
