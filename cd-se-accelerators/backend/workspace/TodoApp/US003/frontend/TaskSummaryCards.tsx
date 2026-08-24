import React from 'react';

interface Props { total: number; completed: number; pending: number; }

export default function TaskSummaryCards({ total, completed, pending }: Props) {
  return (
    <div className="grid grid-cols-3 gap-4">
      <div className="p-4 bg-blue-50 border border-blue-200 rounded-xl">
        <span className="text-xs text-blue-600 uppercase font-bold">Total Tasks</span>
        <p className="text-2xl font-extrabold text-blue-900">{total}</p>
      </div>
      <div className="p-4 bg-emerald-50 border border-emerald-200 rounded-xl">
        <span className="text-xs text-emerald-600 uppercase font-bold">Completed</span>
        <p className="text-2xl font-extrabold text-emerald-900">{completed}</p>
      </div>
      <div className="p-4 bg-amber-50 border border-amber-200 rounded-xl">
        <span className="text-xs text-amber-600 uppercase font-bold">Pending</span>
        <p className="text-2xl font-extrabold text-amber-900">{pending}</p>
      </div>
    </div>
  );
}
