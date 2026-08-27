import React from 'react';

interface EmptyStateProps {
  icon?: React.ReactNode;
  title: string;
  description?: string;
  action?: React.ReactNode;
}

export const EmptyState: React.FC<EmptyStateProps> = ({ icon, title, description, action }) => (
  <div className="flex flex-col items-center justify-center py-12 px-4 text-center">
    {icon && (
      <div className="w-12 h-12 rounded-2xl bg-surface-tertiary flex items-center justify-center mb-4 text-ink-muted">
        {icon}
      </div>
    )}
    <p className="text-sm font-semibold text-ink mb-1">{title}</p>
    {description && <p className="text-xs text-ink-muted max-w-xs mb-4">{description}</p>}
    {action}
  </div>
);
