import React from 'react';
import { useLocation } from 'react-router-dom';

/**
 * Temporary placeholder for pages not yet built.
 * Replace each one with a full implementation over time.
 */
const PlaceholderPage: React.FC = () => {
  const { pathname } = useLocation();
  const pageName = pathname.slice(1).replace(/-/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase()) || 'Dashboard';

  return (
    <div className="p-6 max-w-[1600px] mx-auto">
      <div className="bg-white rounded-2xl border border-surface-border shadow-card p-12 flex flex-col items-center justify-center text-center gap-4">
        <div className="w-16 h-16 rounded-2xl bg-primary-50 flex items-center justify-center">
          <svg className="w-8 h-8 text-primary-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5}
              d="M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z" />
          </svg>
        </div>
        <div>
          <h2 className="text-xl font-bold text-ink">{pageName}</h2>
          <p className="text-sm text-ink-muted mt-1 max-w-sm">
            This page is under construction. The dashboard is fully functional — explore it from the sidebar.
          </p>
        </div>
        <p className="text-xs font-mono text-ink-muted bg-surface-tertiary px-3 py-1.5 rounded-lg">
          Route: {pathname}
        </p>
      </div>
    </div>
  );
};

export default PlaceholderPage;
