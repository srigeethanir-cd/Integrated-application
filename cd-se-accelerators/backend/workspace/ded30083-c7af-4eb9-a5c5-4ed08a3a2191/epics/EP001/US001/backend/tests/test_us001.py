# tests/test_register_patient.py
from fastapi.testclient import TestClient
from main import app
from pydantic import BaseModel
from typing import Optional

class Patient(BaseModel):
    name: str
    email: str
    phone: str
    address: Optional[str]

client = TestClient(app)

def test_register_patient():
    # Test case 1: Receptionist can enter patient details
    patient_data = {
        "name": "John Doe",
        "email": "john@example.com",
        "phone": "1234567890",
        "address": "123 Main St"
    }
    response = client.post("/register-patient", json=patient_data)
    assert response.status_code == 201
    assert response.json()["message"] == "Patient registered successfully"

    # Test case 2: System validates mandatory fields
    patient_data = {
        "email": "jane@example.com",
        "phone": "9876543210"
    }
    response = client.post("/register-patient", json=patient_data)
    assert response.status_code == 400
    assert response.json()["message"] == "Name is required"

    # Test case 3: Unique Patient ID is generated
    patient_data = {
        "name": "Jane Doe",
        "email": "jane@example.com",
        "phone": "9876543210"
    }
    response = client.post("/register-patient", json=patient_data)
    assert response.status_code == 201
    assert "patient_id" in response.json()

    # Test case 4: Patient information is stored successfully
    patient_data = {
        "name": "Bob Smith",
        "email": "bob@example.com",
        "phone": "5555555555"
    }
    response = client.post("/register-patient", json=patient_data)
    assert response.status_code == 201
    assert response.json()["message"] == "Patient registered successfully"

    # Get patient by ID
    patient_id = response.json()["patient_id"]
    response = client.get(f"/patient/{patient_id}")
    assert response.status_code == 200
    assert response.json()["name"] == patient_data["name"]
    assert response.json()["email"] == patient_data["email"]
    assert response.json()["phone"] == patient_data["phone"]