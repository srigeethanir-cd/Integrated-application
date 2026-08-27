import { safeFetch, API_BASE } from './client';

export const workspaceApi = {
  getTree: (storyId: string) =>
    safeFetch<any>(`${API_BASE}/api/v1/workspace/explorer/${storyId}`),

  getFile: (storyId: string, path: string) =>
    safeFetch<any>(`${API_BASE}/api/v1/workspace/explorer/${storyId}/file?path=${encodeURIComponent(path)}`),

  getApis: (storyId: string) =>
    safeFetch<any>(`${API_BASE}/api/v1/workspace/explorer/${storyId}/apis`),

  /** Save (overwrite) a single file in the story workspace. */
  saveFile: (storyId: string, path: string, content: string) =>
    safeFetch<any>(
      `${API_BASE}/api/v1/workspace/explorer/${storyId}/file?path=${encodeURIComponent(path)}`,
      {
        method: 'POST',
        body: JSON.stringify({ content }),
      },
    ),
};
