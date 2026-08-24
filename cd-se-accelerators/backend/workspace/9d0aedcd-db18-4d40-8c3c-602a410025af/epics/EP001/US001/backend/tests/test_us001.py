# tests/test_book_appointment.py
from fastapi.testclient import TestClient
from main import app
from pydantic import BaseModel
from datetime import datetime

class Doctor(BaseModel):
    id: int
    name: str
    specialty: str

class TimeSlot(BaseModel):
    id: int
    start_time: datetime
    end_time: datetime
    doctor_id: int

class Appointment(BaseModel):
    id: int
    patient_name: str
    doctor_id: int
    time_slot_id: int

client = TestClient(app)

def test_book_appointment():
    # Test patient can search available doctors
    response = client.get("/doctors")
    assert response.status_code == 200
    assert len(response.json()) > 0

    # Test patient can select an available time slot
    doctor_id = response.json()[0]["id"]
    response = client.get(f"/doctors/{doctor_id}/time-slots")
    assert response.status_code == 200
    assert len(response.json()) > 0

    # Test appointment confirmation is generated
    time_slot_id = response.json()[0]["id"]
    patient_name = "John Doe"
    response = client.post("/appointments", json={"patient_name": patient_name, "doctor_id": doctor_id, "time_slot_id": time_slot_id})
    assert response.status_code == 201
    assert response.json()["patient_name"] == patient_name
    assert response.json()["doctor_id"] == doctor_id
    assert response.json()["time_slot_id"] == time_slot_id

    # Test doctor schedule is updated automatically
    response = client.get(f"/doctors/{doctor_id}/schedule")
    assert response.status_code == 200
    assert len(response.json()) > 0
    assert response.json()[0]["time_slot_id"] == time_slot_id

def test_book_appointment_invalid_doctor():
    # Test booking appointment with invalid doctor
    doctor_id = 999
    time_slot_id = 1
    patient_name = "John Doe"
    response = client.post("/appointments", json={"patient_name": patient_name, "doctor_id": doctor_id, "time_slot_id": time_slot_id})
    assert response.status_code == 404

def test_book_appointment_invalid_time_slot():
    # Test booking appointment with invalid time slot
    doctor_id = 1
    time_slot_id = 999
    patient_name = "John Doe"
    response = client.post("/appointments", json={"patient_name": patient_name, "doctor_id": doctor_id, "time_slot_id": time_slot_id})
    assert response.status_code == 404