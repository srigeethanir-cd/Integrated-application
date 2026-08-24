typescript
// UserRegistrationComponent.tsx
import React, { useState } from 'react';
import axios from 'axios';

interface UserRegistrationProps {
  // No props for this component
}

const UserRegistrationComponent: React.FC<UserRegistrationProps> = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (password !== confirmPassword) {
      setError('Passwords do not match');
      return;
    }
    try {
      const response = await axios.post('/api/register', {
        email,
        password,
      });
      if (response.status === 201) {
        setSuccess('User registered successfully');
        setError(null);
      } else {
        setError('Failed to register user');
      }
    } catch (error) {
      setError('Failed to register user');
    }
  };

  return (
    <div>
      <h1>User Registration</h1>
      <form onSubmit={handleSubmit}>
        <label>
          Email:
          <input
            type="email"
            value={email}
            onChange={(event) => setEmail(event.target.value)}
          />
        </label>
        <br />
        <label>
          Password:
          <input
            type="password"
            value={password}
            onChange={(event) => setPassword(event.target.value)}
          />
        </label>
        <br />
        <label>
          Confirm Password:
          <input
            type="password"
            value={confirmPassword}
            onChange={(event) => setConfirmPassword(event.target.value)}
          />
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