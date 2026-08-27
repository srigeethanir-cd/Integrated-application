import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { useProjects } from '@/hooks/useDashboard';
import { projectApi } from '@/api/projectApi';
import { Trash2, AlertCircle, RefreshCw } from 'lucide-react';

const statusColor: Record<string, string> = {
  COMPLETED:    'bg-green-100 text-green-700',
  ACTIVE:       'bg-blue-100 text-blue-700',
  GENERATING:   'bg-yellow-100 text-yellow-700',
  READY_TO_MERGE: 'bg-purple-100 text-purple-700',
  EXPORT_READY: 'bg-teal-100 text-teal-700',
};

const ProjectsPage: React.FC = () => {
  const { data: projects, loading, error, refetch } = useProjects();
  const [projectToDelete, setProjectToDelete] = useState<{ id: string; name: string } | null>(null);
  const [isDeleting, setIsDeleting] = useState(false);

  const handleDelete = async () => {
    if (!projectToDelete) return;
    setIsDeleting(true);
    try {
      await projectApi.deleteProject(projectToDelete.id);
      refetch();
    } catch (err) {
      console.error('Failed to delete project:', err);
    } finally {
      setIsDeleting(false);
      setProjectToDelete(null);
    }
  };

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
              <div className="flex items-center gap-4 ml-4 flex-shrink-0">
                <div className="text-right text-[11px] text-ink-muted">
                  <p>Created: {new Date(p.created_at).toLocaleDateString()}</p>
                  <p>Updated: {new Date(p.updated_at).toLocaleDateString()}</p>
                </div>
                <button
                  type="button"
                  onClick={() => setProjectToDelete({ id: p.id, name: p.name })}
                  className="p-2 text-rose-500 hover:text-white bg-rose-50 hover:bg-rose-600 border border-rose-200/80 rounded-xl transition-all cursor-pointer"
                  title={`Delete ${p.name}`}
                >
                  <Trash2 size={15} />
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Confirmation Modal */}
      {projectToDelete && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/60 backdrop-blur-xs p-4 animate-fade-in">
          <div className="bg-white border border-rose-200 rounded-2xl shadow-2xl max-w-md w-full p-6 space-y-4">
            <div className="flex items-start gap-3.5">
              <div className="w-10 h-10 rounded-full bg-rose-100 text-rose-600 flex items-center justify-center shrink-0">
                <Trash2 size={20} />
              </div>
              <div className="flex-1 min-w-0">
                <h3 className="text-base font-bold text-slate-900">Delete Project & Files</h3>
                <p className="text-xs text-slate-500 mt-1">
                  Are you sure you want to delete <strong>{projectToDelete.name}</strong> ({projectToDelete.id})? All database records, workspaces, and zip files will be permanently removed.
                </p>
              </div>
            </div>

            <div className="flex items-center justify-end gap-2.5 pt-2 border-t border-slate-100">
              <button
                type="button"
                disabled={isDeleting}
                onClick={() => setProjectToDelete(null)}
                className="px-4 py-2 text-xs font-semibold text-slate-600 hover:bg-slate-100 rounded-xl transition-colors"
              >
                Cancel
              </button>
              <button
                type="button"
                disabled={isDeleting}
                onClick={handleDelete}
                className="px-4 py-2 text-xs font-semibold text-white bg-rose-600 hover:bg-rose-700 rounded-xl transition-colors inline-flex items-center gap-1.5"
              >
                {isDeleting ? <RefreshCw size={13} className="animate-spin" /> : <Trash2 size={13} />}
                <span>{isDeleting ? 'Deleting...' : 'Yes, Delete'}</span>
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ProjectsPage;

