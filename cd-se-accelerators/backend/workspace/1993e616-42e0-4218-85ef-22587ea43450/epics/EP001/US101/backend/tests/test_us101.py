# tests/test_book_appointment.py
from fastapi.testclient import TestClient
from main import app
from datetime import datetime, timedelta

client = TestClient(app)

def test_book_appointment():
    # Arrange
    doctor_id = 1
    patient_id = 1
    appointment_date = datetime.now() + timedelta(days=1)
    appointment_time = "10:00"

    # Act
    response = client.post(
        "/appointments/",
        json={
            "doctor_id": doctor_id,
            "patient_id": patient_id,
            "appointment_date": appointment_date.strftime("%Y-%m-%d"),
            "appointment_time": appointment_time,
        },
    )

    # Assert
    assert response.status_code == 201
    assert response.json()["message"] == "Appointment booked successfully"

def test_select_doctor():
    # Arrange
    doctor_id = 1

    # Act
    response = client.get(f"/doctors/{doctor_id}")

    # Assert
    assert response.status_code == 200
    assert response.json()["doctor_id"] == doctor_id

def test_select_available_date_and_time():
    # Arrange
    doctor_id = 1
    appointment_date = datetime.now() + timedelta(days=1)
    appointment_time = "10:00"

    # Act
    response = client.get(
        "/doctors/available-slots",
        params={
            "doctor_id": doctor_id,
            "appointment_date": appointment_date.strftime("%Y-%m-%d"),
            "appointment_time": appointment_time,
        },
    )

    # Assert
    assert response.status_code == 200
    assert response.json()["available"] == True

def test_appointment_confirmation():
    # Arrange
    appointment_id = 1

    # Act
    response = client.get(f"/appointments/{appointment_id}")

    # Assert
    assert response.status_code == 200
    assert response.json()["appointment_id"] == appointment_id
    assert response.json()["status"] == "confirmed"