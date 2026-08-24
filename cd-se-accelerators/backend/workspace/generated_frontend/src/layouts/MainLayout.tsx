import React from 'react';
import { Outlet } from 'react-router-dom';

export default function MainLayout() {
  return (
    <div className="flex min-h-screen bg-slate-900">
      <aside className="w-64 bg-slate-800 border-r border-slate-700 p-6">
        <h2 className="text-xl font-bold mb-6 text-white">Menu</h2>
        <nav className="space-y-3">
          <a href="/dashboard" className="block text-slate-300 hover:text-white font-medium">Home</a>
          <a href="/profile" className="block text-slate-400 hover:text-white font-medium">Profile</a>
          <a href="/settings" className="block text-slate-400 hover:text-white font-medium">Setting</a>
        </nav>
      </aside>
      <main className="flex-1 p-8">
        <Outlet />
      </main>
    </div>
  );
}
