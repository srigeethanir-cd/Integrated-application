import { safeFetch, API_BASE } from './client';

/**
 * Backend ExportDeploymentRequest schema (deployment_routes.py):
 *   integrated_project_root: str  (default: "./integrated_project")
 *   output_dir: str               (default: "./outputs/exports")
 *   app_name: str                 (default: "AI_BA_Accelerated_App")
 */
export interface ExportProjectPayload {
  output_dir?: string;
  integrated_project_root?: string;
  app_name?: string;
}

export const exportApi = {
  exportProject: (
    payload: ExportProjectPayload = {
      output_dir: './exports',
      integrated_project_root: './integrated_project',
      app_name: 'AI_BA_Accelerated_App',
    }
  ) =>
    safeFetch<any>(`${API_BASE}/api/v1/deployment/export`, {
      method: 'POST',
      body: JSON.stringify({
        output_dir: payload.output_dir || './exports',
        integrated_project_root: payload.integrated_project_root || './integrated_project',
        app_name: payload.app_name || 'AI_BA_Accelerated_App',
      }),
    }),

  /** URL to directly download the packaged production ZIP from FastAPI backend. */
  getDownloadUrl: (projectId?: string) =>
    `${API_BASE}/api/v1/project/download${projectId ? `?project_id=${projectId}` : ''}`,

  /** Trigger browser download for the generated ZIP file. */
  downloadZip: async (projectId?: string, filename: string = 'project_deployment.zip') => {
    const url = `${API_BASE}/api/v1/project/download${projectId ? `?project_id=${projectId}` : ''}`;
    const res = await fetch(url);
    if (!res.ok) {
      throw new Error(`Failed to download package (status ${res.status})`);
    }
    const blob = await res.blob();
    const blobUrl = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = blobUrl;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    window.URL.revokeObjectURL(blobUrl);
  },
};

