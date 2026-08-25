from fastapi.testclient import TestClient
from main import app
client = TestClient(app)
def test_register_login_and_current_user():
    registration = client.post("/api/auth/register", json={"username": "stageuser", "password": "StrongPassword1", "role": "user"})
    assert registration.status_code in {201, 409}
    login = client.post("/api/auth/login", data={"username": "stageuser", "password": "StrongPassword1"})
    assert login.status_code == 200
    tokens = login.json()
    current = client.get("/api/auth/me", headers={"Authorization": f"Bearer {tokens['access_token']}"})
    assert current.status_code == 200
    assert client.post("/api/auth/refresh", json={"refresh_token": tokens["refresh_token"]}).status_code == 200
def test_authorization_required():
    assert client.get("/api/auth/admin").status_code == 401
