import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { Workspace } from '@/lib/types/project';

interface WorkspaceState {
  workspaces: Workspace[];
  activeWorkspaceId: string | null;
  setActiveWorkspaceId: (id: string | null) => void;
  createWorkspace: (name: string, description: string) => void;
  addWorkspace: (workspace: { id: string; name: string; status?: string; created_at?: string; updated_at?: string }) => void;
  removeWorkspace: (id: string) => void;
  updateWorkspaceStatus: (id: string, status: 'active' | 'completed') => void;
  updateWorkspaceTab: (id: string, tab: string) => void;
}

export const useWorkspaceStore = create<WorkspaceState>()(
  persist(
    (set) => ({
      workspaces: [],
      activeWorkspaceId: null,
      setActiveWorkspaceId: (id) => set({ activeWorkspaceId: id }),
      createWorkspace: (name, description) =>
        set((state) => {
          const baseId = name.toLowerCase().replace(/\s+/g, '-').replace(/[^a-z0-9-]/g, '');
          const existingIds = new Set(state.workspaces.map((w) => w.id));
          const id = existingIds.has(baseId) ? `${baseId}-${Date.now().toString(36)}` : baseId;
          const newWorkspace: Workspace = {
            id,
            name,
            description,
            status: 'active',
            doc_count: 0,
            story_count: 0,
            updated_at: new Date().toLocaleString('en-US', { month: 'short', day: 'numeric', year: 'numeric', hour: 'numeric', minute: '2-digit' }),
          };
          return { workspaces: [newWorkspace, ...state.workspaces] };
        }),
      addWorkspace: (ws) =>
        set((state) => {
          const existingIds = new Set(state.workspaces.map((w) => w.id));
          if (existingIds.has(ws.id)) return state;
          const newWorkspace: Workspace = {
            id: ws.id,
            name: ws.name,
            description: 'Generated workspace',
            status: (ws.status as any) || 'active',
            doc_count: 1,
            story_count: 0,
            updated_at: ws.updated_at || new Date().toLocaleString('en-US', { month: 'short', day: 'numeric', year: 'numeric', hour: 'numeric', minute: '2-digit' }),
          };
          return { workspaces: [newWorkspace, ...state.workspaces] };
        }),
      removeWorkspace: (id) =>
        set((state) => ({ workspaces: state.workspaces.filter((w) => w.id !== id) })),
      updateWorkspaceStatus: (id, status) =>
        set((state) => ({
          workspaces: state.workspaces.map((w) =>
            w.id === id ? { ...w, status } : w
          ),
        })),
      updateWorkspaceTab: (id, tab) =>
        set((state) => ({
          workspaces: state.workspaces.map((w) =>
            w.id === id ? { ...w, last_tab: tab } : w
          ),
        })),
    }),
    { name: 'ba-workspaces' }
  )
);
