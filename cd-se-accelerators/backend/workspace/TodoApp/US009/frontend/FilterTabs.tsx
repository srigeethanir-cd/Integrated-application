import React from 'react';

export default function FilterTabs({ activeFilter, setFilter }: { activeFilter: string; setFilter: (f: string) => void }) {
  const filters = ['All', 'Pending', 'Completed'];
  return (
    <div className="flex gap-2 border-b pb-2">
      {filters.map(f => (
        <button key={f} onClick={() => setFilter(f)} className={`px-4 py-1.5 text-xs font-bold rounded-lg ${activeFilter === f ? 'bg-blue-600 text-white' : 'bg-slate-100 text-slate-600'}`}>
          {f}
        </button>
      ))}
    </div>
  );
}
