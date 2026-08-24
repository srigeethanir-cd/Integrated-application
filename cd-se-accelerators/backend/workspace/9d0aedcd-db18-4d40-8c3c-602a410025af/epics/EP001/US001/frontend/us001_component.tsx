typescript
// BookAppointmentComponent.tsx
import React, { useState, useEffect } from 'react';
import axios from 'axios';

interface Doctor {
  id: number;
  name: string;
  specialty: string;
}

interface TimeSlot {
  id: number;
  startTime: string;
  endTime: string;
  isAvailable: boolean;
}

interface Appointment {
  id: number;
  doctorId: number;
  patientName: string;
  timeSlotId: number;
}

const BookAppointmentComponent = () => {
  const [doctors, setDoctors] = useState<Doctor[]>([]);
  const [selectedDoctor, setSelectedDoctor] = useState<Doctor | null>(null);
  const [timeSlots, setTimeSlots] = useState<TimeSlot[]>([]);
  const [selectedTimeSlot, setSelectedTimeSlot] = useState<TimeSlot | null>(null);
  const [patientName, setPatientName] = useState<string>('');
  const [appointmentConfirmation, setAppointmentConfirmation] = useState<string>('');

  useEffect(() => {
    axios.get('/api/doctors')
      .then(response => {
        setDoctors(response.data);
      })
      .catch(error => {
        console.error(error);
      });
  }, []);

  const handleDoctorSelect = (doctor: Doctor) => {
    setSelectedDoctor(doctor);
    axios.get(`/api/doctors/${doctor.id}/time-slots`)
      .then(response => {
        setTimeSlots(response.data);
      })
      .catch(error => {
        console.error(error);
      });
  };

  const handleTimeSlotSelect = (timeSlot: TimeSlot) => {
    setSelectedTimeSlot(timeSlot);
  };

  const handleBookAppointment = () => {
    if (selectedDoctor && selectedTimeSlot) {
      const appointment: Appointment = {
        id: 0,
        doctorId: selectedDoctor.id,
        patientName: patientName,
        timeSlotId: selectedTimeSlot.id,
      };
      axios.post('/api/appointments', appointment)
        .then(response => {
          setAppointmentConfirmation(`Appointment booked successfully with Dr. ${selectedDoctor.name} at ${selectedTimeSlot.startTime}`);
        })
        .catch(error => {
          console.error(error);
        });
    }
  };

  return (
    <div>
      <h1>Book Appointment</h1>
      <select value={selectedDoctor ? selectedDoctor.id : 0} onChange={(e) => handleDoctorSelect(doctors.find((doctor) => doctor.id === parseInt(e.target.value)) as Doctor)}>
        <option value={0}>Select Doctor</option>
        {doctors.map((doctor) => (
          <option key={doctor.id} value={doctor.id}>{doctor.name}</option>
        ))}
      </select>
      {selectedDoctor && (
        <div>
          <h2>Available Time Slots</h2>
          <select value={selectedTimeSlot ? selectedTimeSlot.id : 0} onChange={(e) => handleTimeSlotSelect(timeSlots.find((timeSlot) => timeSlot.id === parseInt(e.target.value)) as TimeSlot)}>
            <option value={0}>Select Time Slot</option>
            {timeSlots.map((timeSlot) => (
              <option key={timeSlot.id} value={timeSlot.id}>{timeSlot.startTime} - {timeSlot.endTime}</option>
            ))}
          </select>
          <input type="text" value={patientName} onChange={(e) => setPatientName(e.target.value)} placeholder="Enter Patient Name" />
          <button onClick={handleBookAppointment}>Book Appointment</button>
          {appointmentConfirmation && <p>{appointmentConfirmation}</p>}
        </div>
      )}
    </div>
  );
};

export default BookAppointmentComponent;