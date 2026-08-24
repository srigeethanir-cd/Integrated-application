typescript
// AppointmentBooking.tsx
import React, { useState, useEffect } from 'react';
import axios from 'axios';

interface Doctor {
  id: number;
  name: string;
}

interface Appointment {
  id: number;
  doctorId: number;
  date: string;
  time: string;
  patientName: string;
}

const AppointmentBooking = () => {
  const [doctors, setDoctors] = useState<Doctor[]>([]);
  const [selectedDoctor, setSelectedDoctor] = useState<number | null>(null);
  const [date, setDate] = useState<string>('');
  const [time, setTime] = useState<string>('');
  const [patientName, setPatientName] = useState<string>('');
  const [appointment, setAppointment] = useState<Appointment | null>(null);

  useEffect(() => {
    axios.get('/api/doctors')
      .then(response => {
        setDoctors(response.data);
      })
      .catch(error => {
        console.error(error);
      });
  }, []);

  const handleDoctorChange = (event: React.ChangeEvent<HTMLSelectElement>) => {
    setSelectedDoctor(parseInt(event.target.value));
  };

  const handleDateChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    setDate(event.target.value);
  };

  const handleTimeChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    setTime(event.target.value);
  };

  const handlePatientNameChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    setPatientName(event.target.value);
  };

  const handleSubmit = (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const newAppointment: Appointment = {
      id: 0,
      doctorId: selectedDoctor as number,
      date: date,
      time: time,
      patientName: patientName,
    };
    axios.post('/api/appointments', newAppointment)
      .then(response => {
        setAppointment(response.data);
        // Send confirmation notification
        axios.post('/api/notifications', {
          appointmentId: response.data.id,
          patientName: patientName,
        })
          .then(() => {
            console.log('Confirmation notification sent');
          })
          .catch(error => {
            console.error(error);
          });
      })
      .catch(error => {
        console.error(error);
      });
  };

  return (
    <div>
      <h1>Book Appointment</h1>
      <form onSubmit={handleSubmit}>
        <label>
          Select Doctor:
          <select value={selectedDoctor} onChange={handleDoctorChange}>
            <option value="">Select Doctor</option>
            {doctors.map(doctor => (
              <option key={doctor.id} value={doctor.id}>
                {doctor.name}
              </option>
            ))}
          </select>
        </label>
        <br />
        <label>
          Date:
          <input type="date" value={date} onChange={handleDateChange} />
        </label>
        <br />
        <label>
          Time:
          <input type="time" value={time} onChange={handleTimeChange} />
        </label>
        <br />
        <label>
          Patient Name:
          <input type="text" value={patientName} onChange={handlePatientNameChange} />
        </label>
        <br />
        <button type="submit">Book Appointment</button>
      </form>
      {appointment && (
        <div>
          <h2>Appointment Booked Successfully!</h2>
          <p>Doctor: {doctors.find(doctor => doctor.id === appointment.doctorId)?.name}</p>
          <p>Date: {appointment.date}</p>
          <p>Time: {appointment.time}</p>
          <p>Patient Name: {appointment.patientName}</p>
        </div>
      )}
    </div>
  );
};

export default AppointmentBooking;