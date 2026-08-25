from fastapi.testclient import TestClient
from main import app
client = TestClient(app)
def test_upload_and_download():
    response = client.post("/api/files/", data={"label": "notes"}, files={"file": ("notes.txt", b"hello", "text/plain")})
    assert response.status_code == 201
    assert client.get(f"/api/files/{response.json()['id']}").content == b"hello"
def test_mime_validation():
    response = client.post("/api/files/", data={"label": "binary"}, files={"file": ("x.bin", b"x", "application/octet-stream")})
    assert response.status_code == 415
