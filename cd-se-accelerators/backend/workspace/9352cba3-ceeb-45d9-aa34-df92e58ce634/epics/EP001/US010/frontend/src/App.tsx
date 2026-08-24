import React from 'react';
import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';

const LogoutPage: React.FC = () => {
  const navigate = useNavigate();
  const [isLoggingOut, setIsLoggingOut] = useState(false);

  const handleLogout = () => {
    // Invalidate session logic here
    // For demonstration purposes, assume we have a function to invalidate the session
    invalidateSession().then(() => {
      setIsLoggingOut(true);
    });
  };

  useEffect(() => {
    if (isLoggingOut) {
      navigate('/login');
    }
  }, [isLoggingOut, navigate]);

  return (
    <div className="h-screen w-screen flex flex-col items-center justify-center">
      <header className="w-full h-16 bg-primary text-white flex justify-center items-center">
        <h1>Logout Page</h1>
      </header>
      <div className="hero-image h-48 w-full bg-secondary flex justify-center items-center">
        <h2 className="text-2xl text-white">You are about to log out.</h2>
      </div>
      <div className="text-block w-80 h-24 p-4 bg-white text-text flex justify-center items-center">
        <p>Are you sure you want to log out?</p>
      </div>
      <button
        className="call-to-action w-80 h-12 bg-primary text-white rounded-lg flex justify-center items-center"
        onClick={handleLogout}
      >
        Logout
      </button>
    </div>
  );
};

// Mock function to invalidate session
const invalidateSession = () => {
  return new Promise((resolve) => {
    // Simulate session invalidation
    setTimeout(() => {
      resolve();
    }, 1000);
  });
};

export default LogoutPage;