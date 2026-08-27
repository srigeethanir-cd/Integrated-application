import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { API_BASE, safeFetch } from '@/api/client';

const NewProjectPage: React.FC = () => {
  const navigate = useNavigate();
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim()) return;
    setSaving(true);
    setError(null);
    try {
      await safeFetch<any>(`${API_BASE}/api/v1/project/create`, {
        method: 'POST',
        body: JSON.stringify({ name: name.trim(), description: description.trim() || null }),
      });
      navigate('/projects');
    } catch (err: any) {
      setError(err?.message ?? 'Failed to create project');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="p-6 max-w-2xl mx-auto space-y-6">
      <div>
        <h1 className="text-xl font-bold text-ink">New Project</h1>
        <p className="text-sm text-ink-muted mt-1">Create a new BA Accelerator project to start the pipeline.</p>
      </div>

      <form onSubmit={handleCreate} className="bg-white rounded-2xl border border-surface-border shadow-card p-6 space-y-5">
        <div>
          <label className="block text-sm font-semibold text-ink mb-1.5" htmlFor="name">
            Project Name <span className="text-status-danger">*</span>
          </label>
          <input
            id="name"
            type="text"
            required
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="e.g. Employee Management System"
            className="w-full border border-surface-border rounded-xl px-3 py-2.5 text-sm text-ink
              placeholder:text-ink-muted focus:outline-none focus:ring-2 focus:ring-primary-300"
          />
        </div>

        <div>
          <label className="block text-sm font-semibold text-ink mb-1.5" htmlFor="desc">
            Description
          </label>
          <textarea
            id="desc"
            rows={3}
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder="Brief overview of the project goals…"
            className="w-full border border-surface-border rounded-xl px-3 py-2.5 text-sm text-ink
              placeholder:text-ink-muted focus:outline-none focus:ring-2 focus:ring-primary-300 resize-none"
          />
        </div>

        {error && <p className="text-xs text-status-danger">{error}</p>}

        <div className="flex gap-3 justify-end pt-2">
          <button
            type="button"
            onClick={() => navigate('/projects')}
            className="px-4 py-2 text-sm rounded-xl border border-surface-border text-ink-secondary hover:bg-surface-secondary transition-colors"
          >
            Cancel
          </button>
          <button
            type="submit"
            disabled={saving}
            className="px-5 py-2 text-sm font-semibold rounded-xl bg-primary-600 hover:bg-primary-700
              text-white transition-colors disabled:opacity-50"
          >
            {saving ? 'Creating…' : 'Create Project'}
          </button>
        </div>
      </form>
    </div>
  );
};

export default NewProjectPage;
