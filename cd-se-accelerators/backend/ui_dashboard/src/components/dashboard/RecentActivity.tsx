import React from 'react';
import { clsx } from 'clsx';
import {
  ActivityItemSkeleton,
  EmptyState,
  ErrorState,
  SectionHeader,
  ViewAllLink,
} from '@/components/ui';
import { useRecentActivity } from '@/hooks/useDashboard';
import type { ActivityItem, ActivityKind } from '@/services/types';
import { formatDistanceToNow } from 'date-fns';

// ─── Activity icon per kind ───────────────────────────────────────────────────

const kindConfig: Record<
  ActivityKind,
  { bg: string; icon: string; iconEl: React.ReactNode }
> = {
  generation: {
    bg: 'bg-status-successBg',
    icon: 'text-status-success',
    iconEl: (
      <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
          d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
      </svg>
    ),
  },
  approval: {
    bg: 'bg-status-warningBg',
    icon: 'text-status-warning',
    iconEl: (
      <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
          d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
      </svg>
    ),
  },
  blueprint: {
    bg: 'bg-primary-50',
    icon: 'text-primary-600',
    iconEl: (
      <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
          d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z" />
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
          d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
      </svg>
    ),
  },
  merge: {
    bg: 'bg-status-purpleBg',
    icon: 'text-status-purple',
    iconEl: (
      <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
          d="M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4" />
      </svg>
    ),
  },
  database: {
    bg: 'bg-status-tealBg',
    icon: 'text-status-teal',
    iconEl: (
      <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <ellipse cx="12" cy="5" rx="9" ry="3" strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} />
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
          d="M21 12c0 1.657-4.03 3-9 3S3 13.657 3 12M3 5v14c0 1.657 4.03 3 9 3s9-1.343 9-3V5" />
      </svg>
    ),
  },
  validation: {
    bg: 'bg-status-infoBg',
    icon: 'text-status-info',
    iconEl: (
      <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
          d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
      </svg>
    ),
  },
};

// ─── Single activity item ─────────────────────────────────────────────────────

const ActivityRow: React.FC<{ item: ActivityItem; isLast: boolean }> = ({ item, isLast }) => {
  const cfg = kindConfig[item.kind] ?? kindConfig.generation;

  const relativeTime = (() => {
    try {
      return formatDistanceToNow(new Date(item.timestamp), { addSuffix: true });
    } catch {
      return '—';
    }
  })();

  return (
    <div className="flex items-start gap-3 group">
      {/* Icon + connector line */}
      <div className="flex flex-col items-center flex-shrink-0">
        <div
          className={clsx(
            'w-8 h-8 rounded-full flex items-center justify-center transition-transform duration-150 group-hover:scale-110',
            cfg.bg, cfg.icon,
          )}
        >
          {cfg.iconEl}
        </div>
        {!isLast && (
          <div className="w-px flex-1 bg-surface-border mt-1 min-h-[20px]" aria-hidden />
        )}
      </div>

      {/* Text */}
      <div className={clsx('flex-1 min-w-0 pb-4', isLast && 'pb-0')}>
        <p className="text-sm font-semibold text-ink leading-tight truncate">{item.title}</p>
        {item.subtitle && (
          <p className="text-xs text-ink-secondary mt-0.5 truncate">{item.subtitle}</p>
        )}
        <p className="text-[11px] text-primary-500 font-medium mt-1">{relativeTime}</p>
      </div>
    </div>
  );
};

// ─── Horizontal card strip (matches design: 5 items across) ──────────────────

const ActivityCard: React.FC<{ item: ActivityItem }> = ({ item }) => {
  const cfg = kindConfig[item.kind] ?? kindConfig.generation;

  const relativeTime = (() => {
    try {
      return formatDistanceToNow(new Date(item.timestamp), { addSuffix: true });
    } catch {
      return '—';
    }
  })();

  return (
    <div className="flex-1 min-w-[160px] bg-white rounded-2xl border border-surface-border shadow-card p-4
      transition-all duration-200 hover:shadow-card-hover hover:-translate-y-0.5 animate-fade-in">
      <div
        className={clsx(
          'w-8 h-8 rounded-full flex items-center justify-center mb-3',
          cfg.bg, cfg.icon,
        )}
      >
        {cfg.iconEl}
      </div>
      <p className="text-xs font-bold text-ink leading-snug line-clamp-2 mb-1">{item.title}</p>
      {item.subtitle && (
        <p className="text-[11px] text-ink-secondary line-clamp-1 mb-2">{item.subtitle}</p>
      )}
      <p className="text-[11px] font-semibold text-primary-500">{relativeTime}</p>
    </div>
  );
};

// ─── Section ──────────────────────────────────────────────────────────────────

export const RecentActivity: React.FC = () => {
  const { data: activities, loading, error, refetch } = useRecentActivity();

  return (
    <section aria-label="Recent Activity">
      <SectionHeader
        title="Recent Activity"
        action={<ViewAllLink to="/audit" label="View all activity" />}
      />

      {loading && (
        <div className="flex gap-4">
          {Array.from({ length: 5 }).map((_, i) => (
            <div key={i} className="flex-1 min-w-[160px] bg-white rounded-2xl border border-surface-border shadow-card p-4">
              <ActivityItemSkeleton />
            </div>
          ))}
        </div>
      )}

      {error && !loading && (
        <div className="bg-white rounded-2xl border border-surface-border shadow-card p-4">
          <ErrorState message={error} onRetry={refetch} />
        </div>
      )}

      {!loading && !error && (!activities || activities.length === 0) && (
        <div className="bg-white rounded-2xl border border-surface-border shadow-card">
          <EmptyState
            title="No activity yet"
            description="Pipeline activity will appear here as agents run."
            icon={
              <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.8}
                  d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            }
          />
        </div>
      )}

      {!loading && !error && activities && activities.length > 0 && (
        <div
          className="flex gap-3 overflow-x-auto pb-1 -mx-1 px-1
            scrollbar-thin scrollbar-track-transparent scrollbar-thumb-surface-border"
          role="list"
          aria-label="Recent activity items"
        >
          {activities.slice(0, 5).map((item) => (
            <div key={item.id} role="listitem" className="flex-1 min-w-[160px]">
              <ActivityCard item={item} />
            </div>
          ))}
        </div>
      )}
    </section>
  );
};
