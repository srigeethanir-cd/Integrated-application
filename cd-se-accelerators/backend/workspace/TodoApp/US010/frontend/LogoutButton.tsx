import React from 'react';

export default function LogoutButton() {
  const handleLogout = () => {
    localStorage.clear();
    window.location.href = '/login';
  };
  return (
    <button onClick={handleLogout} className="px-4 py-2 bg-red-50 text-red-600 rounded-lg text-sm font-bold border border-red-200 hover:bg-red-100">Log Out</button>
  );
}
