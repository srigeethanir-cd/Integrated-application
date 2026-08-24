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
      setSuccess('User registered successfully');
      setError(null);
    } catch (error: any) {
      if (error.response.status === 400) {
        setError(error.response.data.message);
      } else {
        setError('Failed to register user');
      }
      setSuccess(null);
    }
  };

  return (
    <div>
      <h1>User Registration</h1>
      <form onSubmit={handleSubmit}>
        <div>
          <label>Name:</label>
          <input type="text" value={name} onChange={(e) => setName(e.target.value)} />
        </div>
        <div>
          <label>Email:</label>
          <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} />
        </div>
        <div>
          <label>Password:</label>
          <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} />
        </div>
        <button type="submit">Register</button>
        {error && <p style={{ color: 'red' }}>{error}</p>}
        {success && <p style={{ color: 'green' }}>{success}</p>}
      </form>
    </div>
  );
};

export default UserRegistrationComponent;