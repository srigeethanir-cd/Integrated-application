typescript
// UserRegistrationComponent.tsx
import React, { useState } from 'react';
import axios from 'axios';

interface UserRegistrationForm {
  username: string;
  email: string;
  password: string;
  confirmPassword: string;
}

const UserRegistrationComponent = () => {
  const [form, setForm] = useState<UserRegistrationForm>({
    username: '',
    email: '',
    password: '',
    confirmPassword: '',
  });
  const [errors, setErrors] = useState<any>({});
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    setForm({ ...form, [event.target.name]: event.target.value });
  };

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setErrors({});
    setIsSubmitting(true);

    try {
      const response = await axios.post('/api/register', form);
      if (response.status === 201) {
        // Registration successful, redirect to login page
        window.location.href = '/login';
      } else {
        setErrors(response.data);
      }
    } catch (error: any) {
      setErrors(error.response.data);
    } finally {
      setIsSubmitting(false);
    }
  };

  const validateForm = () => {
    const errors: any = {};
    if (!form.username) {
      errors.username = 'Username is required';
    }
    if (!form.email) {
      errors.email = 'Email is required';
    } else if (!/^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}$/i.test(form.email)) {
      errors.email = 'Invalid email address';
    }
    if (!form.password) {
      errors.password = 'Password is required';
    } else if (form.password.length < 8) {
      errors.password = 'Password must be at least 8 characters';
    }
    if (!form.confirmPassword) {
      errors.confirmPassword = 'Confirm password is required';
    } else if (form.confirmPassword !== form.password) {
      errors.confirmPassword = 'Passwords do not match';
    }
    return errors;
  };

  return (
    <div>
      <h1>User Registration</h1>
      <form onSubmit={handleSubmit}>
        <div>
          <label>Username:</label>
          <input type="text" name="username" value={form.username} onChange={handleChange} />
          {errors.username && <div style={{ color: 'red' }}>{errors.username}</div>}
        </div>
        <div>
          <label>Email:</label>
          <input type="email" name="email" value={form.email} onChange={handleChange} />
          {errors.email && <div style={{ color: 'red' }}>{errors.email}</div>}
        </div>
        <div>
          <label>Password:</label>
          <input type="password" name="password" value={form.password} onChange={handleChange} />
          {errors.password && <div style={{ color: 'red' }}>{errors.password}</div>}
        </div>
        <div>
          <label>Confirm Password:</label>
          <input type="password" name="confirmPassword" value={form.confirmPassword} onChange={handleChange} />
          {errors.confirmPassword && <div style={{ color: 'red' }}>{errors.confirmPassword}</div>}
        </div>
        <button type="submit" disabled={isSubmitting}>
          {isSubmitting ? 'Submitting...' : 'Register'}
        </button>
      </form>
    </div>
  );
};

export default UserRegistrationComponent;