import React from 'react';
import { Link } from 'react-router-dom';
import { useProjects } from '@/hooks/useDashboard';

const statusColor: Record<string, string> = {
  COMPLETED:    'bg-green-100 text-green-700',
  ACTIVE:       'bg-blue-100 text-blue-700',
  GENERATING:   'bg-yellow-100 text-yellow-700',
  READY_TO_MERGE: 'bg-purple-100 text-purple-700',
  EXPORT_READY: 'bg-teal-100 text-teal-700',
};

const ProjectsPage: React.FC = () => {
  const { data: projects, loading, error, refetch } = useProjects();

  return (
    <div className="p-6 max-w-[1600px] mx-auto space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-ink">Projects</h1>
          <p className="text-sm text-ink-muted mt-1">All projects managed by the BA Accelerator pipeline.</p>
        </div>
        <Link
          to="/projects/new"
          className="px-4 py-2 bg-primary-600 hover:bg-primary-700 text-white text-sm font-semibold rounded-xl transition-colors"
        >
          + New Project
        </Link>
      </div>

      {loading && (
        <div className="space-y-3">
          {[...Array(4)].map((_, i) => (
            <div key={i} className="h-20 bg-surface-secondary animate-pulse rounded-2xl" />
          ))}
        </div>
      )}

      {error && !loading && (
        <div className="bg-white rounded-2xl border border-surface-border p-6 text-center">
          <p className="text-status-danger text-sm">{error}</p>
          <button onClick={refetch} className="mt-3 text-primary-600 text-xs hover:underline">Retry</button>
        </div>
      )}

      {!loading && !error && projects && projects.length === 0 && (
        <div className="bg-white rounded-2xl border border-surface-border p-12 text-center">
          <p className="text-ink-muted text-sm">No projects yet. Create one to get started.</p>
        </div>
      )}

      {!loading && !error && projects && projects.length > 0 && (
        <div className="space-y-3">
          {projects.map((p) => (
            <div key={p.id} className="bg-white rounded-2xl border border-surface-border shadow-card p-5 flex items-center justify-between hover:shadow-card-hover transition-shadow">
              <div className="min-w-0 flex-1">
                <div className="flex items-center gap-3 flex-wrap">
                  <h2 className="text-sm font-bold text-ink">{p.name}</h2>
                  <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${statusColor[p.status] ?? 'bg-surface-tertiary text-ink-muted'}`}>
                    {p.status.replace(/_/g, ' ')}
                  </span>
                </div>
                {p.description && (
                  <p className="text-xs text-ink-muted mt-1 truncate">{p.description}</p>
                )}
                <p className="text-[11px] text-ink-muted font-mono mt-1">ID: {p.id}</p>
              </div>
              <div className="text-right text-[11px] text-ink-muted ml-4 flex-shrink-0">
                <p>Created: {new Date(p.created_at).toLocaleDateString()}</p>
                <p>Updated: {new Date(p.updated_at).toLocaleDateString()}</p>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default ProjectsPage;
