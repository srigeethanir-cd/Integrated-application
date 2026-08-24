typescript
// BookAppointmentComponent.tsx
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
}

const BookAppointmentComponent = () => {
  const [doctors, setDoctors] = useState<Doctor[]>([]);
  const [selectedDoctor, setSelectedDoctor] = useState<number | null>(null);
  const [availableDates, setAvailableDates] = useState<string[]>([]);
  const [selectedDate, setSelectedDate] = useState<string | null>(null);
  const [availableTimes, setAvailableTimes] = useState<string[]>([]);
  const [selectedTime, setSelectedTime] = useState<string | null>(null);
  const [appointmentConfirmed, setAppointmentConfirmed] = useState<boolean>(false);

  useEffect(() => {
    axios.get('/api/doctors')
      .then(response => {
        setDoctors(response.data);
      })
      .catch(error => {
        console.error(error);
      });
  }, []);

  const handleDoctorSelect = (doctorId: number) => {
    setSelectedDoctor(doctorId);
    axios.get(`/api/doctors/${doctorId}/available-dates`)
      .then(response => {
        setAvailableDates(response.data);
      })
      .catch(error => {
        console.error(error);
      });
  };

  const handleDateSelect = (date: string) => {
    setSelectedDate(date);
    axios.get(`/api/doctors/${selectedDoctor}/available-times?date=${date}`)
      .then(response => {
        setAvailableTimes(response.data);
      })
      .catch(error => {
        console.error(error);
      });
  };

  const handleTimeSelect = (time: string) => {
    setSelectedTime(time);
  };

  const handleBookAppointment = () => {
    if (selectedDoctor && selectedDate && selectedTime) {
      axios.post('/api/appointments', {
        doctorId: selectedDoctor,
        date: selectedDate,
        time: selectedTime,
      })
        .then(response => {
          setAppointmentConfirmed(true);
        })
        .catch(error => {
          console.error(error);
        });
    }
  };

  return (
    <div>
      <h1>Book Appointment</h1>
      <select value={selectedDoctor} onChange={(e) => handleDoctorSelect(Number(e.target.value))}>
        <option value="">Select Doctor</option>
        {doctors.map((doctor) => (
          <option key={doctor.id} value={doctor.id}>{doctor.name}</option>
        ))}
      </select>
      {selectedDoctor && (
        <select value={selectedDate} onChange={(e) => handleDateSelect(e.target.value)}>
          <option value="">Select Date</option>
          {availableDates.map((date) => (
            <option key={date} value={date}>{date}</option>
          ))}
        </select>
      )}
      {selectedDate && (
        <select value={selectedTime} onChange={(e) => handleTimeSelect(e.target.value)}>
          <option value="">Select Time</option>
          {availableTimes.map((time) => (
            <option key={time} value={time}>{time}</option>
          ))}
        </select>
      )}
      <button onClick={handleBookAppointment}>Book Appointment</button>
      {appointmentConfirmed && (
        <p>Appointment booked successfully!</p>
      )}
    </div>
  );
};

export default BookAppointmentComponent;