import React, { useState } from 'react';

export const UserProfileComponent: React.FC = () => {
  const [status, setStatus] = useState<string | null>(null);

  return (
    <div className="p-6 bg-white rounded-2xl shadow-sm border border-slate-200">
      <span className="text-[10px] font-bold tracking-wider text-indigo-600 bg-indigo-50 px-2.5 py-1 rounded-full uppercase">
        US004 • Module
      </span>
      <h2 className="text-xl font-bold text-slate-800 mt-2">Account Lockout</h2>
      <p className="text-xs text-slate-500 mt-1">Interactive component for Account Lockout.</p>
      
      <button 
        className="mt-4 px-4 py-2 bg-indigo-600 text-white text-xs font-bold rounded-lg shadow-sm hover:bg-indigo-700 transition"
        onClick={() => setStatus("Operation completed at " + new Date().toLocaleTimeString())}
      >
        Execute Action
      </button>
      
      {status && (
        <div className="mt-3 p-3 bg-emerald-50 border border-emerald-200 text-emerald-800 text-xs font-semibold rounded-lg">
          ✓ {status}
        </div>
      )}
    </div>
  );
};

export default UserProfileComponent;
