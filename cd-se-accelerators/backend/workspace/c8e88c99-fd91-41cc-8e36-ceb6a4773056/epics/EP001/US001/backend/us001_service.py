from fastapi import FastAPI, HTTPException, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List
from datetime import datetime
from fastapi_mail import FastMail, MessageSchema
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm

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

# Define the Appointment request model
class AppointmentRequest(BaseModel):
    doctor_id: int
    date: str
    time: str

# In-memory data store for doctors and appointments
doctors = [
    Doctor(id=1, name="John Doe", specialty="Cardiology"),
    Doctor(id=2, name="Jane Doe", specialty="Neurology"),
]

appointments = []

# OAuth2 password bearer
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Define the token endpoint
@app.post("/token")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    # Replace with actual authentication logic
    return {"access_token": "fake_token", "token_type": "bearer"}

# Define the endpoint to get available doctors
@app.get("/doctors", dependencies=[Depends(oauth2_scheme)])
async def get_doctors():
    return doctors

# Define the endpoint to book an appointment
@app.post("/appointments", dependencies=[Depends(oauth2_scheme)])
async def book_appointment(appointment_request: AppointmentRequest):
    # Validate the appointment request
    if appointment_request.doctor_id not in [doctor.id for doctor in doctors]:
        raise HTTPException(status_code=400, detail="Invalid doctor ID")

    # Save the appointment
    new_appointment = Appointment(
        id=len(appointments) + 1,
        patient_name="John Doe",  # Replace with actual patient name
        doctor_id=appointment_request.doctor_id,
        date=appointment_request.date,
        time=appointment_request.time,
    )
    appointments.append(new_appointment)

    # Send a confirmation notification
    message = MessageSchema(
        subject="Appointment Confirmation",
        recipients=["patient@example.com"],  # Replace with actual patient email
        body=f"Your appointment with Dr. {next((doctor.name for doctor in doctors if doctor.id == appointment_request.doctor_id), 'Unknown')} has been scheduled for {appointment_request.date} at {appointment_request.time}.",
    )
    fm = FastMail("your_email@example.com")  # Replace with actual email
    await fm.send_message(message)

    return JSONResponse(content={"message": "Appointment booked successfully"}, status_code=201)

# Define the endpoint to get appointments
@app.get("/appointments", dependencies=[Depends(oauth2_scheme)])
async def get_appointments():
    return appointments