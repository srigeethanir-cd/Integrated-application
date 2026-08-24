import React, { useState } from 'react';

export const ViewDashboardComponent: React.FC = () => {
  const [refreshCount, setRefreshCount] = useState(0);

  return (
    <div className="p-6 bg-white rounded-2xl border border-slate-200 shadow-sm space-y-5 font-sans">
      <div className="flex justify-between items-center border-b border-slate-100 pb-3">
        <div>
          <span className="text-xs font-bold text-indigo-600 uppercase tracking-wider">US003</span>
          <h2 className="text-lg font-black text-slate-800">View Dashboard</h2>
        </div>
        <button
          onClick={() => setRefreshCount(prev => prev + 1)}
          className="px-3 py-1.5 bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-bold rounded-lg transition-all"
        >
          ⟳ Refresh
        </button>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
        <div className="p-3.5 bg-indigo-50 rounded-xl border border-indigo-100 text-center">
          <div className="text-[10px] uppercase font-bold text-indigo-500">Total Users</div>
          <div className="text-xl font-black text-indigo-900 mt-1">1,248</div>
        </div>
        <div className="p-3.5 bg-emerald-50 rounded-xl border border-emerald-100 text-center">
          <div className="text-[10px] uppercase font-bold text-emerald-600">Active Sessions</div>
          <div className="text-xl font-black text-emerald-900 mt-1">84</div>
        </div>
        <div className="p-3.5 bg-orange-50 rounded-xl border border-orange-100 text-center">
          <div className="text-[10px] uppercase font-bold text-orange-500">System Health</div>
          <div className="text-xl font-black text-orange-900 mt-1">99.8%</div>
        </div>
      </div>
    </div>
  );
};

export default ViewDashboardComponent;
