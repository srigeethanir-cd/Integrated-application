# tests/test_employee_dashboard.py
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_employee_dashboard():
    response = client.get("/employee/dashboard")
    assert response.status_code == 200
    assert "data" in response.json()

def test_employee_dashboard_data():
    response = client.get("/employee/dashboard")
    data = response.json()["data"]
    assert len(data) > 0

def test_employee_dashboard_empty_data():
    # simulate empty data
    response = client.get("/employee/dashboard?empty=true")
    data = response.json()["data"]
    assert len(data) == 0

def test_employee_dashboard_invalid_request():
    response = client.get("/employee/dashboard?invalid=true")
    assert response.status_code == 400

def test_employee_dashboard_unauthorized_request():
    response = client.get("/employee/dashboard", headers={"Authorization": "Invalid"})
    assert response.status_code == 401