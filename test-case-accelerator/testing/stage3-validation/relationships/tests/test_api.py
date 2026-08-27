from fastapi.testclient import TestClient
from main import app
client = TestClient(app)
def test_author_and_missing_author_book():
    assert client.post("/api/library/authors", json={"name": "Octavia"}).status_code == 201
    response = client.post("/api/library/authors/999/books", json={"title": "Novel", "isbn": "1234567890", "publisher_name": "Press"})
    assert response.status_code == 404
