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

# Define the Appointment model
class Appointment(BaseModel):
    id: int
    patient_name: str
    doctor_id: int
    date: str
    time: str

# Define the Appointment Request model
class AppointmentRequest(BaseModel):
    doctor_id: int
    date: str
    time: str

# In-memory data store for doctors and appointments
doctors: List[Doctor] = [
    Doctor(id=1, name="John Doe", specialty="Cardiology"),
    Doctor(id=2, name="Jane Smith", specialty="Neurology"),
]

appointments: List[Appointment] = []

# Get all doctors
@app.get("/doctors")
async def get_doctors():
    return doctors

# Get available doctors for a specific date
@app.get("/doctors/available")
async def get_available_doctors(date: str):
    available_doctors = []
    for doctor in doctors:
        is_available = True
        for appointment in appointments:
            if appointment.doctor_id == doctor.id and appointment.date == date:
                is_available = False
                break
        if is_available:
            available_doctors.append(doctor)
    return available_doctors

# Book an appointment
@app.post("/appointments")
async def book_appointment(appointment_request: AppointmentRequest):
    # Check if the doctor is available
    doctor = next((d for d in doctors if d.id == appointment_request.doctor_id), None)
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")

    # Check if the appointment time is available
    for appointment in appointments:
        if appointment.doctor_id == appointment_request.doctor_id and appointment.date == appointment_request.date and appointment.time == appointment_request.time:
            raise HTTPException(status_code=400, detail="Appointment time is not available")

    # Create a new appointment
    new_appointment = Appointment(
        id=len(appointments) + 1,
        patient_name="John Doe",  # Replace with the actual patient name
        doctor_id=appointment_request.doctor_id,
        date=appointment_request.date,
        time=appointment_request.time,
    )
    appointments.append(new_appointment)
    return new_appointment

# Get all appointments
@app.get("/appointments")
async def get_appointments():
    return appointments