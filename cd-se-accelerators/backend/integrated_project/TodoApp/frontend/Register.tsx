import React, { useState } from 'react';
import RegisterForm from './RegisterForm';

export default function Register() {
  return (
    <div className="max-w-md mx-auto p-6 bg-white rounded-xl shadow-md">
      <h2 className="text-2xl font-bold mb-4">Create Todo Account</h2>
      <RegisterForm />
    </div>
  );
}
