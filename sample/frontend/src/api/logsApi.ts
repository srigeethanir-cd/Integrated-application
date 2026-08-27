import { safeFetch, API_BASE } from './client';

export const logsApi = {
  getLogs: (storyId: string) =>
    safeFetch<any>(`${API_BASE}/api/v1/workspace/story/${storyId}/logs`),
};
