import React from 'react';

export default function SearchBar({ query, setQuery }: { query: string; setQuery: (q: string) => void }) {
  return (
    <div className="relative w-full max-w-md">
      <input type="text" placeholder="Search tasks by title..." value={query} onChange={e => setQuery(e.target.value)} className="w-full pl-9 pr-4 py-2 border rounded-xl bg-slate-50 focus:bg-white text-sm" />
    </div>
  );
}
