import React from 'react';
import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';

const Logout: React.FC = () => {
  const navigate = useNavigate();
  const [isLoggedOut, setIsLoggedOut] = useState(false);

  const handleLogout = () => {
    // Invalidate session
    localStorage.removeItem('session');
    setIsLoggedOut(true);
  };

  useEffect(() => {
    if (isLoggedOut) {
      // Redirect to login page
      navigate('/login');
    }
  }, [isLoggedOut, navigate]);

  return (
    <div className="flex justify-center items-center h-screen">
      <button
        className="bg-primary hover:bg-primary-dark text-white font-bold py-2 px-4 rounded"
        onClick={handleLogout}
      >
        Logout
      </button>
    </div>
  );
};

export default Logout;