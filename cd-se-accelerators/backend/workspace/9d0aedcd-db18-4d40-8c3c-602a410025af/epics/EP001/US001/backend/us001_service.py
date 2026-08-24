from fastapi import FastAPI, HTTPException, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List
from datetime import datetime, timedelta
from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Database Connection
SQLALCHEMY_DATABASE_URL = "sqlite:///database.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# Models
class Doctor(Base):
    __tablename__ = "doctors"
    id = Column(Integer, primary_key=True)
    name = Column(String)
    specialty = Column(String)

class Appointment(Base):
    __tablename__ = "appointments"
    id = Column(Integer, primary_key=True)
    doctor_id = Column(Integer)
    patient_name = Column(String)
    appointment_time = Column(DateTime)

Base.metadata.create_all(bind=engine)

# Schemas
class DoctorSchema(BaseModel):
    id: int
    name: str
    specialty: str

class AppointmentSchema(BaseModel):
    doctor_id: int
    patient_name: str
    appointment_time: datetime

class AppointmentResponseSchema(BaseModel):
    id: int
    doctor_id: int
    patient_name: str
    appointment_time: datetime

# FastAPI App
app = FastAPI()

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Endpoints
@app.get("/doctors/")
def read_doctors(db: SessionLocal = Depends(get_db)):
    doctors = db.query(Doctor).all()
    return [DoctorSchema(id=doctor.id, name=doctor.name, specialty=doctor.specialty) for doctor in doctors]

@app.post("/appointments/")
def create_appointment(appointment: AppointmentSchema, db: SessionLocal = Depends(get_db)):
    doctor = db.query(Doctor).filter(Doctor.id == appointment.doctor_id).first()
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")
    
    existing_appointment = db.query(Appointment).filter(Appointment.doctor_id == appointment.doctor_id, Appointment.appointment_time == appointment.appointment_time).first()
    if existing_appointment:
        raise HTTPException(status_code=400, detail="Time slot is already taken")
    
    new_appointment = Appointment(doctor_id=appointment.doctor_id, patient_name=appointment.patient_name, appointment_time=appointment.appointment_time)
    db.add(new_appointment)
    db.commit()
    db.refresh(new_appointment)
    
    return AppointmentResponseSchema(id=new_appointment.id, doctor_id=new_appointment.doctor_id, patient_name=new_appointment.patient_name, appointment_time=new_appointment.appointment_time)

@app.get("/appointments/{appointment_id}")
def read_appointment(appointment_id: int, db: SessionLocal = Depends(get_db)):
    appointment = db.query(Appointment).filter(Appointment.id == appointment_id).first()
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")
    
    return AppointmentResponseSchema(id=appointment.id, doctor_id=appointment.doctor_id, patient_name=appointment.patient_name, appointment_time=appointment.appointment_time)

@app.get("/doctors/{doctor_id}/available-time-slots")
def read_available_time_slots(doctor_id: int, db: SessionLocal = Depends(get_db)):
    doctor = db.query(Doctor).filter(Doctor.id == doctor_id).first()
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")
    
    appointments = db.query(Appointment).filter(Appointment.doctor_id == doctor_id).all()
    available_time_slots = []
    for hour in range(9, 17):
        for minute in [0, 30]:
            appointment_time = datetime.now().replace(hour=hour, minute=minute, second=0)
            if not any(appointment.appointment_time == appointment_time for appointment in appointments):
                available_time_slots.append(appointment_time)
    
    return available_time_slots