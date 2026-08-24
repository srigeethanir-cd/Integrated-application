import React, { useRef } from 'react';
import { clsx } from 'clsx';
import {
  CircularProgress,
  Badge,
  EpicCardSkeleton,
  EmptyState,
  ErrorState,
  SectionHeader,
  ViewAllLink,
} from '@/components/ui';
import type { CircularVariant } from '@/components/ui';
import { useEnrichedEpics } from '@/hooks/useDashboard';
import type { Epic } from '@/services/types';

// ─── Status → visual config ───────────────────────────────────────────────────

type EpicStatusLabel = 'On Track' | 'In Progress' | 'Behind' | 'Completed';

const statusConfig: Record<
  EpicStatusLabel,
  { badgeVariant: 'success' | 'info' | 'warning' | 'teal'; dot: boolean; progressVariant: CircularVariant }
> = {
  'On Track':   { badgeVariant: 'success', dot: true, progressVariant: 'success' },
  'In Progress':{ badgeVariant: 'info',    dot: true, progressVariant: 'primary' },
  'Behind':     { badgeVariant: 'warning', dot: true, progressVariant: 'orange'  },
  'Completed':  { badgeVariant: 'teal',    dot: true, progressVariant: 'teal'    },
};

// Assign a distinct icon colour per epic index
const epicIconVariants = [
  { bg: 'bg-primary-50',          icon: 'text-primary-600'   },
  { bg: 'bg-green-50',            icon: 'text-green-600'     },
  { bg: 'bg-status-orangeBg',     icon: 'text-status-orange' },
  { bg: 'bg-status-purpleBg',     icon: 'text-status-purple' },
  { bg: 'bg-status-tealBg',       icon: 'text-status-teal'   },
];

const progressBarVariants: CircularVariant[] = [
  'primary', 'success', 'orange', 'purple', 'teal',
];

// ─── Epic card ────────────────────────────────────────────────────────────────

const EpicCard: React.FC<{ epic: Epic; index: number }> = ({ epic, index }) => {
  const status       = (epic.status_label ?? 'In Progress') as EpicStatusLabel;
  const cfg          = statusConfig[status] ?? statusConfig['In Progress'];
  const pct          = epic.progress_percentage ?? 0;
  const circVariant  = progressBarVariants[index % progressBarVariants.length];
  const iconCls      = epicIconVariants[index % epicIconVariants.length];
  const total        = epic.total_stories      ?? 0;
  const completed    = epic.completed_stories  ?? 0;
  const pending      = epic.pending_stories    ?? 0;

  // Progress bar colour for bottom strip
  const stripColor: Record<CircularVariant, string> = {
    primary: 'bg-primary-500',
    success: 'bg-status-success',
    warning: 'bg-status-warning',
    danger:  'bg-status-danger',
    purple:  'bg-status-purple',
    orange:  'bg-status-orange',
    teal:    'bg-status-teal',
  };

  return (
    <div
      className={clsx(
        'bg-white rounded-2xl border border-surface-border shadow-card p-5 min-w-[220px] max-w-[260px] flex-shrink-0',
        'transition-all duration-200 hover:shadow-card-hover hover:-translate-y-0.5',
        'animate-fade-in',
      )}
    >
      {/* Icon + circular progress */}
      <div className="flex items-start justify-between mb-3">
        <div className={clsx('w-10 h-10 rounded-xl flex items-center justify-center', iconCls.bg)}>
          <svg
            className={clsx('w-5 h-5', iconCls.icon)}
            fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.8}
          >
            <path strokeLinecap="round" strokeLinejoin="round"
              d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
          </svg>
        </div>

        <CircularProgress
          value={pct}
          size={56}
          strokeWidth={5}
          variant={circVariant}
        />
      </div>

      {/* Title + description */}
      <h3 className="text-sm font-bold text-ink leading-tight mb-1">{epic.title}</h3>
      {epic.description && (
        <p className="text-xs text-ink-muted leading-relaxed line-clamp-2 mb-3">
          {epic.description}
        </p>
      )}

      {/* Thin progress strip */}
      <div className="h-1 w-full bg-surface-tertiary rounded-full overflow-hidden mb-3">
        <div
          className={clsx('h-full rounded-full transition-all duration-700', stripColor[circVariant])}
          style={{ width: `${pct}%` }}
        />
      </div>

      {/* Story counts */}
      <div className="grid grid-cols-3 gap-2 mb-3">
        {[
          { label: 'Stories',   value: total },
          { label: 'Completed', value: completed },
          { label: 'Pending',   value: pending, accent: pending > 0 },
        ].map(({ label, value, accent }) => (
          <div key={label} className="text-center">
            <p className={clsx(
              'text-sm font-extrabold leading-tight tabular-nums',
              accent ? 'text-status-orange' : 'text-ink',
            )}>
              {value}
            </p>
            <p className="text-[10px] text-ink-muted">{label}</p>
          </div>
        ))}
      </div>

      {/* Status badge */}
      <Badge variant={cfg.badgeVariant} dot size="md" className="w-full justify-center">
        {status}
      </Badge>
    </div>
  );
};

// ─── Horizontal scroll container ─────────────────────────────────────────────

export const EpicsOverview: React.FC = () => {
  const { data: epics, loading, error, refetch } = useEnrichedEpics();
  const scrollRef = useRef<HTMLDivElement>(null);

  return (
    <section aria-label="Epics Overview">
      <SectionHeader
        title="Epics Overview"
        action={<ViewAllLink to="/epics" label="View all epics" />}
      />

      {loading && (
        <div className="flex gap-4 overflow-x-auto pb-2">
          {Array.from({ length: 5 }).map((_, i) => (
            <EpicCardSkeleton key={i} />
          ))}
        </div>
      )}

      {error && !loading && (
        <div className="bg-white rounded-2xl border border-surface-border shadow-card p-4">
          <ErrorState message={error} onRetry={refetch} />
        </div>
      )}

      {!loading && !error && (!epics || epics.length === 0) && (
        <div className="bg-white rounded-2xl border border-surface-border shadow-card">
          <EmptyState
            title="No epics yet"
            description="Run the AI pipeline to generate epics from your user stories."
            icon={
              <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.8}
                  d="M3 7a2 2 0 012-2h4l2 2h8a2 2 0 012 2v8a2 2 0 01-2 2H5a2 2 0 01-2-2V7z" />
              </svg>
            }
          />
        </div>
      )}

      {!loading && !error && epics && epics.length > 0 && (
        <div
          ref={scrollRef}
          className="flex gap-4 overflow-x-auto pb-2 -mx-1 px-1 snap-x snap-mandatory
            scrollbar-thin scrollbar-track-transparent scrollbar-thumb-surface-border"
          role="list"
          aria-label="Epic cards"
        >
          {epics.map((epic, i) => (
            <div key={epic.id} role="listitem" className="snap-start">
              <EpicCard epic={epic} index={i} />
            </div>
          ))}
        </div>
      )}
    </section>
  );
};
