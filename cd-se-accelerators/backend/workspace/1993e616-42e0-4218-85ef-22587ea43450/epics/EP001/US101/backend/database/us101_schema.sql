python
# models.py
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class Doctor(Base):
    __tablename__ = 'doctors'
    id = Column(Integer, primary_key=True)
    name = Column(String)
    specialty = Column(String)

class Appointment(Base):
    __tablename__ = 'appointments'
    id = Column(Integer, primary_key=True)
    doctor_id = Column(Integer, ForeignKey('doctors.id'))
    doctor = relationship('Doctor', backref='appointments')
    patient_name = Column(String)
    appointment_date = Column(DateTime)
    appointment_time = Column(String)

class Patient(Base):
    __tablename__ = 'patients'
    id = Column(Integer, primary_key=True)
    name = Column(String)
    appointments = relationship('Appointment', backref='patient')

# database.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base

engine = create_engine('sqlite:///database.db')
Base.metadata.create_all(engine)

Session = sessionmaker(bind=engine)
session = Session()

# schemas.py
from pydantic import BaseModel
from datetime import datetime

class DoctorSchema(BaseModel):
    id: int
    name: str
    specialty: str

class AppointmentSchema(BaseModel):
    doctor_id: int
    patient_name: str
    appointment_date: datetime
    appointment_time: str

class PatientSchema(BaseModel):
    id: int
    name: str

# main.py
from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from database import session
from schemas import DoctorSchema, AppointmentSchema, PatientSchema
from models import Doctor, Appointment, Patient
from typing import List

app = FastAPI()

def get_db():
    db = session
    try:
        yield db
    finally:
        db.close()

@app.get("/doctors/")
def read_doctors(db: Session = Depends(get_db)):
    return db.query(Doctor).all()

@app.post("/appointments/")
def create_appointment(appointment: AppointmentSchema, db: Session = Depends(get_db)):
    doctor = db.query(Doctor).filter(Doctor.id == appointment.doctor_id).first()
    if not doctor:
        return {"error": "Doctor not found"}
    new_appointment = Appointment(doctor_id=appointment.doctor_id, patient_name=appointment.patient_name, appointment_date=appointment.appointment_date, appointment_time=appointment.appointment_time)
    db.add(new_appointment)
    db.commit()
    db.refresh(new_appointment)
    return {"message": "Appointment created successfully"}

@app.get("/appointments/")
def read_appointments(db: Session = Depends(get_db)):
    return db.query(Appointment).all()

@app.get("/patients/")
def read_patients(db: Session = Depends(get_db)):
    return db.query(Patient).all()

@app.post("/patients/")
def create_patient(patient: PatientSchema, db: Session = Depends(get_db)):
    new_patient = Patient(name=patient.name)
    db.add(new_patient)
    db.commit()
    db.refresh(new_patient)
    return {"message": "Patient created successfully"}