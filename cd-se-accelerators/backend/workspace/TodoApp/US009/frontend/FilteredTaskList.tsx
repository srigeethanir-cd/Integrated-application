import React from 'react';

export default function FilteredTaskList({ filter }: { filter: string }) {
  return (
    <div className="p-4 bg-white rounded-xl shadow-sm border mt-4">
      <p className="text-xs font-bold text-slate-500 uppercase">Showing: {filter} Tasks</p>
    </div>
  );
}
