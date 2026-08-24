typescript
// UserRegistrationComponent.tsx
import React, { useState } from 'react';
import axios from 'axios';

interface UserRegistrationProps {
  // No props for this component
}

const UserRegistrationComponent: React.FC<UserRegistrationProps> = () => {
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    try {
      const response = await axios.post('/api/register', {
        name,
        email,
        password,
      });
      setSuccess('Registration successful!');
      setError(null);
    } catch (error: any) {
      if (error.response.status === 400) {
        setError('Email already exists');
      } else {
        setError('Registration failed');
      }
      setSuccess(null);
    }
  };

  return (
    <div>
      <h2>Register</h2>
      <form onSubmit={handleSubmit}>
        <label>
          Name:
          <input type="text" value={name} onChange={(e) => setName(e.target.value)} />
        </label>
        <br />
        <label>
          Email:
          <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} />
        </label>
        <br />
        <label>
          Password:
          <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} />
        </label>
        <br />
        <button type="submit">Register</button>
      </form>
      {error && <p style={{ color: 'red' }}>{error}</p>}
      {success && <p style={{ color: 'green' }}>{success}</p>}
    </div>
  );
};

export default UserRegistrationComponent;