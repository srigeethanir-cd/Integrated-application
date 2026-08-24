import React from 'react';
import LoginForm from './LoginForm';

export default function Login() {
  return (
    <div className="max-w-md mx-auto p-6 bg-white rounded-xl shadow-md">
      <h2 className="text-2xl font-bold mb-4 font-sans">Login to Todo App</h2>
      <LoginForm />
    </div>
  );
}
