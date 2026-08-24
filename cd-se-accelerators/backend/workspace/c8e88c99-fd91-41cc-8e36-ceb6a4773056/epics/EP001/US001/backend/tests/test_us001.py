# tests/test_book_appointment.py
from fastapi.testclient import TestClient
from main import app
from datetime import datetime, timedelta
import json

client = TestClient(app)

def test_book_appointment():
    # Test patient can view available doctors
    response = client.get("/doctors")
    assert response.status_code == 200
    assert len(response.json()) > 0

    # Test patient can select date and time
    doctor_id = response.json()[0]["id"]
    date = datetime.now() + timedelta(days=1)
    time = "10:00"
    response = client.get(f"/doctors/{doctor_id}/available-times?date={date.strftime('%Y-%m-%d')}")
    assert response.status_code == 200
    assert len(response.json()) > 0
    assert time in response.json()

    # Test appointment is saved successfully
    patient_name = "John Doe"
    patient_email = "johndoe@example.com"
    appointment_data = {
        "doctor_id": doctor_id,
        "date": date.strftime("%Y-%m-%d"),
        "time": time,
        "patient_name": patient_name,
        "patient_email": patient_email
    }
    response = client.post("/appointments", json=appointment_data)
    assert response.status_code == 201
    assert response.json()["id"] is not None

    # Test confirmation notification is sent
    # For simplicity, we assume the notification is sent via email
    # and we have a separate endpoint to check if the email was sent
    response = client.get(f"/appointments/{response.json()['id']}/notification")
    assert response.status_code == 200
    assert response.json()["sent"] is True

def test_book_appointment_invalid_doctor():
    # Test booking appointment with invalid doctor id
    doctor_id = "invalid-doctor-id"
    date = datetime.now() + timedelta(days=1)
    time = "10:00"
    response = client.get(f"/doctors/{doctor_id}/available-times?date={date.strftime('%Y-%m-%d')}")
    assert response.status_code == 404

def test_book_appointment_invalid_date():
    # Test booking appointment with invalid date
    doctor_id = 1
    date = "invalid-date"
    time = "10:00"
    response = client.get(f"/doctors/{doctor_id}/available-times?date={date}")
    assert response.status_code == 400

def test_book_appointment_invalid_time():
    # Test booking appointment with invalid time
    doctor_id = 1
    date = datetime.now() + timedelta(days=1)
    time = "invalid-time"
    response = client.get(f"/doctors/{doctor_id}/available-times?date={date.strftime('%Y-%m-%d')}")
    assert response.status_code == 200
    assert time not in response.json()