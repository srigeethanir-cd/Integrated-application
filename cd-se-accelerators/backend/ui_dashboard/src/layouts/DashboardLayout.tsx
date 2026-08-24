import React from 'react';
import { Outlet } from 'react-router-dom';
import { Sidebar } from '@/components/layout/Sidebar';
import { TopBar } from '@/components/layout/TopBar';

/**
 * Root layout: fixed sidebar on left, scrollable main area on right.
 * All dashboard pages are rendered inside <Outlet />.
 */
const DashboardLayout: React.FC = () => (
  <div className="flex h-screen bg-surface-secondary overflow-hidden font-sans">
    {/* Fixed sidebar */}
    <Sidebar />

    {/* Main content — scrolls independently */}
    <div className="flex flex-col flex-1 min-w-0 overflow-hidden">
      <TopBar />
      <main className="flex-1 overflow-y-auto">
        <Outlet />
      </main>
    </div>
  </div>
);

export default DashboardLayout;
