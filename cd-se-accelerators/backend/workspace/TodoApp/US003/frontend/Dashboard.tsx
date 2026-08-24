import React from 'react';
import TaskSummaryCards from './TaskSummaryCards';

export default function Dashboard() {
  return (
    <div className="p-6 space-y-6 bg-slate-50 min-h-screen">
      <h1 className="text-3xl font-bold text-slate-800">Todo Dashboard</h1>
      <TaskSummaryCards total={12} completed={8} pending={4} />
    </div>
  );
}
