typescript
// PatientRegistrationComponent.tsx
import React, { useState } from 'react';
import axios from 'axios';

interface Patient {
  name: string;
  email: string;
  phone: string;
  address: string;
}

const PatientRegistrationComponent = () => {
  const [patient, setPatient] = useState<Patient>({
    name: '',
    email: '',
    phone: '',
    address: '',
  });
  const [patientId, setPatientId] = useState('');
  const [error, setError] = useState('');

  const handleInputChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = event.target;
    setPatient({ ...patient, [name]: value });
  };

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    try {
      if (!patient.name || !patient.email || !patient.phone || !patient.address) {
        setError('Please fill in all mandatory fields.');
        return;
      }
      const response = await axios.post('http://localhost:8000/patients', patient);
      setPatientId(response.data.patientId);
      setPatient({
        name: '',
        email: '',
        phone: '',
        address: '',
      });
      setError('');
    } catch (error) {
      setError('Failed to register patient.');
    }
  };

  return (
    <div>
      <h2>Patient Registration</h2>
      <form onSubmit={handleSubmit}>
        <label>Name:</label>
        <input type="text" name="name" value={patient.name} onChange={handleInputChange} />
        <br />
        <label>Email:</label>
        <input type="email" name="email" value={patient.email} onChange={handleInputChange} />
        <br />
        <label>Phone:</label>
        <input type="text" name="phone" value={patient.phone} onChange={handleInputChange} />
        <br />
        <label>Address:</label>
        <input type="text" name="address" value={patient.address} onChange={handleInputChange} />
        <br />
        <button type="submit">Register Patient</button>
      </form>
      {patientId && <p>Patient ID: {patientId}</p>}
      {error && <p style={{ color: 'red' }}>{error}</p>}
    </div>
  );
};

export default PatientRegistrationComponent;