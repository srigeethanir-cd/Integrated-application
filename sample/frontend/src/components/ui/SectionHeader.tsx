import React from 'react';

interface SectionHeaderProps {
  title: string;
  action?: React.ReactNode;
}

export const SectionHeader: React.FC<SectionHeaderProps> = ({ title, action }) => (
  <div className="flex items-center justify-between mb-4">
    <h2 className="text-base font-bold text-ink">{title}</h2>
    {action}
  </div>
);
