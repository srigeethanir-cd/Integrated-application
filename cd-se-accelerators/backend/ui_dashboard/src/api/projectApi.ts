import { safeFetch, API_BASE } from './client';

export interface ProjectConfigPayload {
  configuration_json: {
    id: string;
    frontend: string;
    backend: string;
    database: string;
    orm: string;
    pipelineMode?: string;
  };
}

export interface ProjectRequirementsPayload {
  requirement_json: {
    user_stories: any[];
  };
}

export interface ProjectWireframePayload {
  wireframe_spec: {
    filename: string;
    size: string;
    status: string;
    type?: string;
  };
}

export const projectApi = {
  listProjects: () =>
    safeFetch<any>(`${API_BASE}/api/v1/projects`),

  createProject: (projectName: string, description?: string) =>
    safeFetch<any>(`${API_BASE}/api/v1/project/create`, {
      method: 'POST',
      body: JSON.stringify({ project_name: projectName, description }),
    }),

  uploadConfig: (payload: ProjectConfigPayload, projectId?: string) =>
    safeFetch<any>(`${API_BASE}/api/v1/project/upload-config${projectId ? `?project_id=${projectId}` : ''}`, {
      method: 'POST',
      body: JSON.stringify(payload),
    }),

  uploadRequirements: (payload: ProjectRequirementsPayload, projectId?: string) =>
    safeFetch<any>(`${API_BASE}/api/v1/project/upload-requirements${projectId ? `?project_id=${projectId}` : ''}`, {
      method: 'POST',
      body: JSON.stringify(payload),
    }),

  uploadWireframe: (payload: ProjectWireframePayload, projectId?: string) =>
    safeFetch<any>(`${API_BASE}/api/v1/project/upload-wireframe${projectId ? `?project_id=${projectId}` : ''}`, {
      method: 'POST',
      body: JSON.stringify(payload),
    }),

  getStatus: (projectId?: string) =>
    safeFetch<any>(`${API_BASE}/api/v1/project/status${projectId ? `?project_id=${projectId}` : ''}`),

  runStage1: (projectId?: string) =>
    safeFetch<any>(`${API_BASE}/api/v1/project/run${projectId ? `?project_id=${projectId}` : ''}`, {
      method: 'POST',
    }),

  updateProject: (projectId: string, payload: any) =>
    safeFetch<any>(`${API_BASE}/api/v1/projects/${projectId}`, {
      method: 'PATCH',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(payload),
    }),

  canMerge: (projectId: string) =>
    safeFetch<any>(`${API_BASE}/api/v1/project/can-merge?project_id=${projectId}`),

  continueToMerge: (projectId: string) =>
    safeFetch<any>(`${API_BASE}/api/v1/project/continue-to-merge?project_id=${projectId}`, {
      method: 'POST',
    }),
};
