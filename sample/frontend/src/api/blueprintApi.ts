import { safeFetch, API_BASE } from './client';

export interface ApproveBlueprintPayload {
  approved: boolean;
  comments: string;
}

export const blueprintApi = {
  getBlueprint: (projectId?: string) =>
    safeFetch<any>(`${API_BASE}/api/v1/blueprints${projectId ? `?project_id=${projectId}` : ''}`),

  approveBlueprint: (payload: ApproveBlueprintPayload, projectId?: string) =>
    safeFetch<any>(`${API_BASE}/api/v1/project/approve-blueprint${projectId ? `?project_id=${projectId}` : ''}`, {
      method: 'POST',
      body: JSON.stringify(payload),
    }),
};
