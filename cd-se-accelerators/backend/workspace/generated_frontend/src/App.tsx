import React from 'react';
import AppRoutes from './routes/AppRoutes';
import './index.css';

export default function App() {
  return (
    <div className="min-h-screen bg-slate-900 text-slate-100 font-sans antialiased">
      <AppRoutes />
    </div>
  );
}
