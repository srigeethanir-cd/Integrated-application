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

    appointments = relationship("Appointment", back_populates="doctor")

class Appointment(Base):
    __tablename__ = 'appointments'
    id = Column(Integer, primary_key=True)
    doctor_id = Column(Integer, ForeignKey('doctors.id'))
    patient_name = Column(String)
    appointment_time = Column(DateTime)

    doctor = relationship("Doctor", back_populates="appointments")

class AvailableTimeSlot(Base):
    __tablename__ = 'available_time_slots'
    id = Column(Integer, primary_key=True)
    doctor_id = Column(Integer, ForeignKey('doctors.id'))
    time_slot = Column(DateTime)

    doctor = relationship("Doctor", backref="available_time_slots")