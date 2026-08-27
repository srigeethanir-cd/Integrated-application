import { safeFetch, API_BASE } from './client';

export const traceabilityApi = {
  getTraceability: (projectId?: string) =>
    safeFetch<any>(`${API_BASE}/api/v1/project/traceability${projectId ? `?project_id=${projectId}` : ''}`),
};

