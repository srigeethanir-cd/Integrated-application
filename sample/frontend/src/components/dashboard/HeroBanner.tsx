import React from 'react';
import { clsx } from 'clsx';
import { Badge, ProgressBar, HeroBannerSkeleton, ErrorState } from '@/components/ui';
import { usePipelineStatus, useProjects } from '@/hooks/useDashboard';
import { formatDistanceToNow } from 'date-fns';

// ─── Tech stack pill ──────────────────────────────────────────────────────────

const stackIcons: Record<string, React.ReactNode> = {
  python: (
    <svg className="w-3.5 h-3.5" viewBox="0 0 24 24" fill="currentColor">
      <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-1 14H9V8h2v8zm4 0h-2V8h2v8z"/>
    </svg>
  ),
  react: (
    <svg className="w-3.5 h-3.5" viewBox="0 0 24 24" fill="currentColor">
      <circle cx="12" cy="12" r="2.5"/>
      <ellipse cx="12" cy="12" rx="10" ry="4" fill="none" stroke="currentColor" strokeWidth="1.5"/>
      <ellipse cx="12" cy="12" rx="10" ry="4" fill="none" stroke="currentColor" strokeWidth="1.5"
        transform="rotate(60 12 12)"/>
      <ellipse cx="12" cy="12" rx="10" ry="4" fill="none" stroke="currentColor" strokeWidth="1.5"
        transform="rotate(120 12 12)"/>
    </svg>
  ),
  postgresql: (
    <svg className="w-3.5 h-3.5" viewBox="0 0 24 24" fill="currentColor">
      <path d="M12 2C8.13 2 5 5.13 5 9v6c0 3.87 3.13 7 7 7s7-3.13 7-7V9c0-3.87-3.13-7-7-7z"/>
    </svg>
  ),
};

function getTechPills(techStack: Record<string, string> | string | null): string[] {
  if (!techStack) return ['Python FastAPI', 'React TypeScript', 'PostgreSQL'];
  if (typeof techStack === 'string') {
    return techStack.split('/').map((s) => s.trim()).filter(Boolean);
  }
  return Object.values(techStack).filter(Boolean);
}

function pillIcon(label: string): React.ReactNode {
  const l = label.toLowerCase();
  if (l.includes('python') || l.includes('fastapi')) return stackIcons.python;
  if (l.includes('react') || l.includes('typescript')) return stackIcons.react;
  if (l.includes('postgres') || l.includes('sql')) return stackIcons.postgresql;
  return null;
}

function pillColor(label: string): string {
  const l = label.toLowerCase();
  if (l.includes('python') || l.includes('fastapi')) return 'bg-blue-50 text-blue-700 border-blue-100';
  if (l.includes('react') || l.includes('typescript')) return 'bg-sky-50 text-sky-700 border-sky-100';
  if (l.includes('postgres') || l.includes('sql')) return 'bg-indigo-50 text-indigo-700 border-indigo-100';
  return 'bg-surface-tertiary text-ink-secondary border-surface-border';
}

// ─── Decorative chart SVG ─────────────────────────────────────────────────────

const DecorativeChart: React.FC<{ pct: number }> = ({ pct }) => (
  <div className="absolute right-0 top-0 h-full w-52 overflow-hidden pointer-events-none select-none hidden md:flex items-center justify-end pr-4">
    {/* Soft gradient blob */}
    <div className="absolute inset-0 bg-gradient-to-l from-primary-50 via-primary-50/30 to-transparent" />
    {/* SVG illustration */}
    <svg viewBox="0 0 200 140" className="w-48 h-36 relative z-10 drop-shadow-sm" aria-hidden>
      {/* Chart bars */}
      {[30, 55, 40, 75, 60, 85, pct].map((h, i) => (
        <rect
          key={i}
          x={10 + i * 26}
          y={140 - h * 1.1}
          width={18}
          height={h * 1.1}
          rx={4}
          className={i === 6 ? 'fill-primary-500' : 'fill-primary-200'}
          opacity={i === 6 ? 1 : 0.7}
        />
      ))}
      {/* Top badge on last bar */}
      <rect x="158" y="12" width="34" height="18" rx="6" className="fill-primary-600" />
      <text x="175" y="25" textAnchor="middle" className="fill-white" fontSize="9" fontWeight="700">
        {pct}%
      </text>
    </svg>
  </div>
);

// ─── Main component ───────────────────────────────────────────────────────────

export const HeroBanner: React.FC = () => {
  const { data: pipeline, loading: pipelineLoading, error: pipelineError, refetch } = usePipelineStatus();
  const { data: projects, loading: projectsLoading } = useProjects();

  const loading = pipelineLoading || projectsLoading;

  if (loading) return <HeroBannerSkeleton />;
  if (pipelineError) return (
    <div className="bg-white rounded-2xl border border-surface-border shadow-card p-5">
      <ErrorState message={pipelineError} onRetry={refetch} />
    </div>
  );

  const projectName  = pipeline?.project_name  ?? projects?.[0]?.name ?? 'Employee Management System';
  const projectId    = pipeline?.project_id     ?? projects?.[0]?.id   ?? '—';
  const progress     = pipeline?.progress_percentage ?? 0;
  const status       = pipeline?.execution_status ?? projects?.[0]?.status ?? 'ACTIVE';
  const updatedAt    = projects?.[0]?.updated_at;
  const techStack    = projects?.[0]?.tech_stack ?? null;

  const techPills = getTechPills(techStack);
  const progressVariant: 'primary' | 'success' | 'warning' =
    progress >= 80 ? 'success' : progress >= 40 ? 'primary' : 'warning';

  const shortId = typeof projectId === 'string'
    ? `PRJ-${projectId.slice(0, 8).toUpperCase()}`
    : 'PRJ-EMP-001';

  const lastUpdated = updatedAt
    ? formatDistanceToNow(new Date(updatedAt), { addSuffix: true })
    : '—';

  const isActive = !['FAILED', 'REJECTED_BY_BA', 'VALIDATION_FAILED'].includes(status);

  return (
    <div className="relative bg-white rounded-2xl border border-surface-border shadow-hero overflow-hidden">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-0">

        {/* ── Left: Project info ─────────────────────────────────────── */}
        <div className="p-6 pr-4">
          <p className="text-[10px] font-bold uppercase tracking-widest text-primary-600 mb-2">
            Current Project
          </p>

          <div className="flex items-center gap-2.5 flex-wrap">
            <h2 className="text-2xl font-extrabold text-ink leading-tight">{projectName}</h2>
            <Badge variant={isActive ? 'active' : 'danger'} dot>
              {isActive ? 'Active' : status.replace(/_/g, ' ')}
            </Badge>
          </div>

          <p className="text-xs text-ink-muted mt-1.5 mb-4">
            Created{updatedAt ? ` on ${new Date(updatedAt).toLocaleDateString('en-US', { day: '2-digit', month: 'short', year: 'numeric' })}` : ''}
            {' '}•{' '}
            Project ID: <span className="font-mono font-medium text-ink-secondary">{shortId}</span>
          </p>

          {/* Tech stack pills */}
          <div className="flex flex-wrap gap-2">
            {techPills.map((label) => (
              <span
                key={label}
                className={clsx(
                  'inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg border text-xs font-medium',
                  pillColor(label),
                )}
              >
                {pillIcon(label)}
                {label}
              </span>
            ))}
          </div>
        </div>

        {/* ── Right: Progress ───────────────────────────────────────── */}
        <div className="relative p-6 pl-4 border-t md:border-t-0 md:border-l border-surface-border flex flex-col justify-center overflow-hidden">
          <p className="text-[10px] font-bold uppercase tracking-widest text-primary-600 mb-3 relative z-10">
            Overall Progress
          </p>

          <div className="flex items-end gap-2 relative z-10 mb-3">
            <span className="text-5xl font-extrabold text-ink leading-none tabular-nums">
              {progress}
            </span>
            <span className="text-2xl font-bold text-ink-secondary mb-1">%</span>
          </div>

          <div className="relative z-10 mb-3">
            <ProgressBar value={progress} variant={progressVariant} size="md" animated />
          </div>

          <p className="text-xs text-ink-muted relative z-10">
            Last updated: {lastUpdated}
          </p>

          {/* Decorative chart */}
          <DecorativeChart pct={Math.round(progress)} />
        </div>
      </div>
    </div>
  );
};
