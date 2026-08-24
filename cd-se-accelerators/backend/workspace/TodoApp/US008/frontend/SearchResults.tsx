import React from 'react';

export default function SearchResults({ results }: { results: any[] }) {
  return (
    <div className="space-y-2 mt-4">
      {results.map((task: any) => (
        <div key={task.id} className="p-3 bg-white border rounded-lg flex justify-between">
          <span className="font-semibold text-slate-800">{task.title}</span>
          <span className="text-xs text-slate-400">{task.status}</span>
        </div>
      ))}
    </div>
  );
}
