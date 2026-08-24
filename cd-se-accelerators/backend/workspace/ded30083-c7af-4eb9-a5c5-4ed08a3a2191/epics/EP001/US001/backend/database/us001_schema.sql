python
# models.py
from pydantic import BaseModel, Field
from typing import Optional
from uuid import UUID, uuid4

class Patient(BaseModel):
    id: Optional[UUID] = Field(default_factory=uuid4, alias="patient_id")
    name: str
    email: str
    phone: str
    address: str

    class Config:
        allow_population_by_field_name = True

# database.py
from sqlalchemy import create_engine, Column, String, Integer
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects.postgresql import UUID

SQLALCHEMY_DATABASE_URL = "postgresql://user:password@localhost/patient_db"

engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

class PatientDB(Base):
    __tablename__ = "patients"
    id = Column(UUID(as_uuid=True), primary_key=True)
    name = Column(String)
    email = Column(String)
    phone = Column(String)
    address = Column(String)

Base.metadata.create_all(bind=engine)

# crud.py
from models import Patient
from database import SessionLocal, PatientDB

def create_patient(db: SessionLocal, patient: Patient):
    db_patient = PatientDB(
        id=patient.id,
        name=patient.name,
        email=patient.email,
        phone=patient.phone,
        address=patient.address
    )
    db.add(db_patient)
    db.commit()
    db.refresh(db_patient)
    return db_patient

def get_patient(db: SessionLocal, patient_id: UUID):
    return db.query(PatientDB).filter(PatientDB.id == patient_id).first()

# main.py
from fastapi import FastAPI, HTTPException
from pydantic import ValidationError
from crud import create_patient
from models import Patient
from database import SessionLocal

app = FastAPI()

@app.post("/patients/")
async def register_patient(patient: Patient):
    try:
        db = SessionLocal()
        db_patient = create_patient(db, patient)
        return {"patient_id": db_patient.id}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# schema.sql
CREATE TABLE IF NOT EXISTS patients (
    id UUID PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    phone VARCHAR(20) NOT NULL,
    address TEXT NOT NULL
);