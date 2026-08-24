from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from uuid import uuid4
from typing import Optional

app = FastAPI()

class Patient(BaseModel):
    name: str
    email: str
    phone: str
    address: Optional[str]

# In-memory patient database for simplicity
# In a real application, use a database like PostgreSQL or MongoDB
patients = {}

@app.post("/patients/")
async def create_patient(patient: Patient):
    # Validate mandatory fields
    if not patient.name or not patient.email or not patient.phone:
        raise HTTPException(status_code=400, detail="Name, email, and phone are mandatory fields")

    # Generate unique patient ID
    patient_id = str(uuid4())

    # Store patient information
    patients[patient_id] = patient.dict()

    return {"patient_id": patient_id}

@app.get("/patients/{patient_id}")
async def get_patient(patient_id: str):
    if patient_id not in patients:
        raise HTTPException(status_code=404, detail="Patient not found")
    return patients[patient_id]