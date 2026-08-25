from fastapi.testclient import TestClient
from main import app
client = TestClient(app)
def test_dependency_failure():
    response = client.post("/api/jobs/", headers={"x-dependency-state": "down"}, json={"name": "Import"})
    assert response.status_code == 503
def test_nested_not_found():
    assert client.put("/api/jobs/999?state=done").status_code == 404
