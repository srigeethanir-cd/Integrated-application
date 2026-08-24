import React from 'react';
import { Link } from 'react-router-dom';

interface ViewAllLinkProps {
  to: string;
  label?: string;
}

export const ViewAllLink: React.FC<ViewAllLinkProps> = ({ to, label = 'View all' }) => (
  <Link
    to={to}
    className="inline-flex items-center gap-1 text-xs font-semibold text-primary-600 hover:text-primary-700 transition-colors"
  >
    {label}
    <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M9 5l7 7-7 7" />
    </svg>
  </Link>
);
