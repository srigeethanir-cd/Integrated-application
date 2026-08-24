import { safeFetch, API_BASE } from './client';

export interface RequestChangePayload {
  project_id: string;
  blueprint_id?: string;
  blueprint_version?: number;
  location_type: string;
  target_id?: string;
  target_path?: string;
  field_name?: string;
  requested_change: string;
  created_by?: string;
}

export const requestChangeApi = {
  create: (payload: RequestChangePayload) =>
    safeFetch<any>(`${API_BASE}/api/v1/request-changes/`, {
      method: 'POST',
      body: JSON.stringify(payload),
    }),

  list: (projectId: string) =>
    safeFetch<any>(`${API_BASE}/api/v1/request-changes/?project_id=${projectId}`),

  apply: (requestChangeId: string) =>
    safeFetch<any>(`${API_BASE}/api/v1/request-changes/${requestChangeId}/apply`, {
      method: 'POST',
    }),
};
