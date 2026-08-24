import { safeFetch, API_BASE } from './client';

export const mergeApi = {
  /**
   * Step 1 — Trigger end-to-end project integration via workflow router.
   * Route: POST /api/v1/project/integrate
   * Sends project_id in the request BODY (backend reads from ExecutionState, not query param).
   */
  integrate: (projectId?: string) =>
    safeFetch<any>(`${API_BASE}/api/v1/project/integrate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(projectId ? { project_id: projectId } : {}),
    }),

  /**
   * Step 2 — Execute Agent 3 integration & validation directly.
   * Route: POST /api/v1/agents/agent3/run
   * This triggers Agent3MergeValidation.run_integration() on the backend.
   */
  runAgent3: (workspaceRoot?: string, integratedProjectRoot?: string) =>
    safeFetch<any>(`${API_BASE}/api/v1/agents/agent3/run`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        workspace_root: workspaceRoot || './workspace',
        integrated_project_root: integratedProjectRoot || './integrated_project',
      }),
    }),

  /**
   * Step 3 — Merge all approved stories into integrated_project/TodoApp.
   * Route: POST /api/v1/workspace/merge  (workspace_routes.py)
   */
  merge: () =>
    safeFetch<any>(`${API_BASE}/api/v1/workspace/merge`, {
      method: 'POST',
    }),

  /**
   * Poll merge/integration status.
   * Route: GET /api/v1/workspace/merge/status
   */
  getStatus: () =>
    safeFetch<any>(`${API_BASE}/api/v1/workspace/merge/status`),
};
