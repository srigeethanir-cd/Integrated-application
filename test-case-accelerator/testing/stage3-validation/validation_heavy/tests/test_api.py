from fastapi.testclient import TestClient
from main import app
client = TestClient(app)
def test_rejects_invalid_profile():
    assert client.post("/api/profiles/", json={"username": "X", "email": "bad", "password": "short", "age": 10, "tags": []}).status_code == 422
def test_lists_profiles():
    assert client.get("/api/profiles/").status_code == 200
