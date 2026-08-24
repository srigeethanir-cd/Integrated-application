from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List
from datetime import datetime

app = FastAPI()

# Define the Doctor model
class Doctor(BaseModel):
    id: int
    name: str
    specialty: str
    available_time_slots: List[str]

# Define the Appointment model
class Appointment(BaseModel):
    id: int
    patient_name: str
    doctor_id: int
    time_slot: str

# Define the Appointment Request model
class AppointmentRequest(BaseModel):
    patient_name: str
    doctor_id: int
    time_slot: str

# In-memory data store for doctors and appointments
doctors = [
    Doctor(id=1, name="John Doe", specialty="Cardiology", available_time_slots=["09:00", "10:00", "11:00"]),
    Doctor(id=2, name="Jane Smith", specialty="Neurology", available_time_slots=["09:00", "10:00", "11:00"]),
]

appointments = []

# API endpoint to search available doctors
@app.get("/doctors")
async def search_doctors():
    return doctors

# API endpoint to book an appointment
@app.post("/appointments")
async def book_appointment(appointment_request: AppointmentRequest):
    # Find the selected doctor
    doctor = next((d for d in doctors if d.id == appointment_request.doctor_id), None)
    if doctor is None:
        raise HTTPException(status_code=404, detail="Doctor not found")

    # Check if the selected time slot is available
    if appointment_request.time_slot not in doctor.available_time_slots:
        raise HTTPException(status_code=400, detail="Time slot is not available")

    # Create a new appointment
    new_appointment = Appointment(
        id=len(appointments) + 1,
        patient_name=appointment_request.patient_name,
        doctor_id=appointment_request.doctor_id,
        time_slot=appointment_request.time_slot,
    )

    # Add the new appointment to the list of appointments
    appointments.append(new_appointment)

    # Update the doctor's available time slots
    doctor.available_time_slots.remove(appointment_request.time_slot)

    # Return the appointment confirmation
    return {"appointment_id": new_appointment.id, "confirmation": f"Appointment booked with Dr. {doctor.name} at {appointment_request.time_slot}"}

# API endpoint to get appointment by id
@app.get("/appointments/{appointment_id}")
async def get_appointment(appointment_id: int):
    appointment = next((a for a in appointments if a.id == appointment_id), None)
    if appointment is None:
        raise HTTPException(status_code=404, detail="Appointment not found")
    return appointment