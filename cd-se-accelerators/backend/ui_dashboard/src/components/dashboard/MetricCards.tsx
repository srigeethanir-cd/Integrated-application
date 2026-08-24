import React from 'react';
import { Link } from 'react-router-dom';
import { clsx } from 'clsx';
import { IconBox, MetricCardSkeleton, ErrorState } from '@/components/ui';
import type { IconBoxVariant } from '@/components/ui';
import { useDashboardSummary } from '@/hooks/useDashboard';

// ─── Single metric card ───────────────────────────────────────────────────────

interface MetricCardProps {
  value: number | string;
  label: string;
  sublabel: string;
  icon: React.ReactNode;
  iconVariant: IconBoxVariant;
  linkTo: string;
  linkLabel: string;
  animationDelay?: number;
}

const MetricCard: React.FC<MetricCardProps> = ({
  value,
  label,
  sublabel,
  icon,
  iconVariant,
  linkTo,
  linkLabel,
  animationDelay = 0,
}) => (
  <div
    className="bg-white rounded-2xl border border-surface-border shadow-card p-5 animate-fade-in
      transition-all duration-200 hover:shadow-card-hover hover:-translate-y-0.5"
    style={{ animationDelay: `${animationDelay}ms` }}
  >
    <div className="flex items-start gap-3">
      <IconBox variant={iconVariant} size="md">
        {icon}
      </IconBox>
      <div className="flex-1 min-w-0">
        <p className="text-2xl font-extrabold text-ink leading-tight tabular-nums">{value}</p>
        <p className="text-sm font-semibold text-ink mt-0.5">{label}</p>
      </div>
    </div>
    <div className="mt-3 pt-3 border-t border-surface-border flex items-center justify-between">
      <p className="text-xs text-ink-muted">{sublabel}</p>
      <Link
        to={linkTo}
        className="inline-flex items-center gap-1 text-xs font-semibold text-primary-600 hover:text-primary-700 transition-colors whitespace-nowrap"
      >
        {linkLabel}
        <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M9 5l7 7-7 7" />
        </svg>
      </Link>
    </div>
  </div>
);

// ─── Icon SVG definitions ─────────────────────────────────────────────────────

const EpicIcon = () => (
  <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.8}>
    <path strokeLinecap="round" strokeLinejoin="round"
      d="M3 7a2 2 0 012-2h4l2 2h8a2 2 0 012 2v8a2 2 0 01-2 2H5a2 2 0 01-2-2V7z" />
  </svg>
);

const StoryIcon = () => (
  <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.8}>
    <path strokeLinecap="round" strokeLinejoin="round"
      d="M4 6h16M4 10h16M4 14h8" />
  </svg>
);

const CompletedIcon = () => (
  <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.8}>
    <path strokeLinecap="round" strokeLinejoin="round"
      d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
  </svg>
);

const PendingIcon = () => (
  <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.8}>
    <path strokeLinecap="round" strokeLinejoin="round"
      d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
  </svg>
);

const InProgressIcon = () => (
  <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.8}>
    <path strokeLinecap="round" strokeLinejoin="round"
      d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
  </svg>
);

const FilesIcon = () => (
  <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.8}>
    <path strokeLinecap="round" strokeLinejoin="round"
      d="M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4" />
  </svg>
);

// ─── Grid of all 6 cards ──────────────────────────────────────────────────────

export const MetricCards: React.FC = () => {
  const { data, loading, error, refetch } = useDashboardSummary();

  if (loading) {
    return (
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-4">
        {Array.from({ length: 6 }).map((_, i) => (
          <MetricCardSkeleton key={i} />
        ))}
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-white rounded-2xl border border-surface-border shadow-card p-4">
        <ErrorState message={error} onRetry={refetch} />
      </div>
    );
  }

  const completedPct = data ? `${data.completed_percentage}%` : '—';

  const cards: (Omit<MetricCardProps, 'animationDelay'>)[] = [
    {
      value:       data?.total_epics ?? 0,
      label:       'Epics',
      sublabel:    'View all epics →',
      icon:        <EpicIcon />,
      iconVariant: 'blue',
      linkTo:      '/epics',
      linkLabel:   'View all epics',
    },
    {
      value:       data?.total_stories ?? 0,
      label:       'User Stories',
      sublabel:    'View all stories →',
      icon:        <StoryIcon />,
      iconVariant: 'indigo',
      linkTo:      '/epics',
      linkLabel:   'View all stories',
    },
    {
      value:       data?.completed_stories ?? 0,
      label:       'Completed',
      sublabel:    `${completedPct} of total`,
      icon:        <CompletedIcon />,
      iconVariant: 'green',
      linkTo:      '/epics?status=completed',
      linkLabel:   'View completed',
    },
    {
      value:       data?.pending_approval ?? 0,
      label:       'Pending Approval',
      sublabel:    'Needs your review',
      icon:        <PendingIcon />,
      iconVariant: 'orange',
      linkTo:      '/approvals',
      linkLabel:   'Review now',
    },
    {
      value:       data?.in_progress ?? 0,
      label:       'In Progress',
      sublabel:    'Currently running',
      icon:        <InProgressIcon />,
      iconVariant: 'teal',
      linkTo:      '/pipeline',
      linkLabel:   'View pipeline',
    },
    {
      value:       data?.generated_files ?? 0,
      label:       'Generated Files',
      sublabel:    'Across all stories',
      icon:        <FilesIcon />,
      iconVariant: 'purple',
      linkTo:      '/artifacts',
      linkLabel:   'Browse files',
    },
  ];

  return (
    <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-4">
      {cards.map((card, i) => (
        <MetricCard key={card.label} {...card} animationDelay={i * 60} />
      ))}
    </div>
  );
};
