from fastapi.testclient import TestClient

from main import app


def test_authentication_crud_contract() -> None:
    with TestClient(app) as client:
        created = client.post("/api/v1/authentication", json={"name": "example", "data": {"role": "user"}})
        assert created.status_code == 201
        record = created.json()

        listed = client.get("/api/v1/authentication?page=1&page_size=20")
        assert listed.status_code == 200
        assert listed.json()["total"] >= 1

        updated = client.put(f"/api/v1/authentication/{record['id']}", json={"name": "updated"})
        assert updated.status_code == 200
        assert updated.json()["name"] == "updated"

        deleted = client.delete(f"/api/v1/authentication/{record['id']}")
        assert deleted.status_code == 204
