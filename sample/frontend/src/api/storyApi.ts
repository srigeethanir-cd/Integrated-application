import { safeFetch, API_BASE } from './client';

/**
 * Story API — routes hierarchy:
 *  - Audit-critical actions (approve/reject/regenerate/versions) → DB-backed story_routes.py
 *    at /api/v1/stories/{id}/... (writes StoryLifecycle + StoryHistory records)
 *  - Execution/runtime data (status/logs) → workspace_routes.py at /api/v1/workspace/story/{id}/...
 */
export const storyApi = {
  /** List workspace stories (runtime pipeline data). */
  getStories: () =>
    safeFetch<any>(`${API_BASE}/api/v1/workspace/stories`),

  /** Detailed metadata for a single workspace story. */
  getStoryDetails: (storyId: string) =>
    safeFetch<any>(`${API_BASE}/api/v1/workspace/story/${storyId}`),

  /**
   * Approve a story — DB-backed route (story_routes.py).
   * Persists StoryLifecycle APPROVED record + StoryHistory audit entry.
   * Falls back to workspace route for workspace-only stories.
   */
  approveStory: async (storyId: string) => {
    try {
      return await safeFetch<any>(`${API_BASE}/api/v1/stories/${storyId}/approve`, {
        method: 'POST',
      });
    } catch {
      return safeFetch<any>(`${API_BASE}/api/v1/workspace/story/${storyId}/approve`, {
        method: 'POST',
      });
    }
  },

  /**
   * Reject a story — DB-backed route (story_routes.py).
   * Persists StoryLifecycle REJECTED record + StoryHistory audit entry.
   */
  rejectStory: async (storyId: string, reason: string) => {
    try {
      return await safeFetch<any>(`${API_BASE}/api/v1/stories/${storyId}/reject`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ reason }),
      });
    } catch {
      return safeFetch<any>(`${API_BASE}/api/v1/workspace/story/${storyId}/reject`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ reason }),
      });
    }
  },

  /**
   * Regenerate a story — DB-backed route (story_routes.py).
   * Increments version, stores StoryRefinement prompt, and launches
   * a background Agent-2 targeted regeneration task.
   */
  regenerateStory: async (storyId: string, refinement_prompt: string) => {
    try {
      return await safeFetch<any>(`${API_BASE}/api/v1/stories/${storyId}/regenerate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ refinement_prompt }),
      });
    } catch {
      return safeFetch<any>(`${API_BASE}/api/v1/workspace/story/${storyId}/regenerate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ refinement_prompt }),
      });
    }
  },

  /**
   * Retrieve full audit/version history — DB-backed route (story_routes.py).
   * Returns all StoryHistory + StoryRefinement records ordered by version desc.
   * Route: GET /api/v1/stories/{id}/versions
   */
  getStoryVersions: async (storyId: string) => {
    try {
      const data = await safeFetch<any>(`${API_BASE}/api/v1/stories/${storyId}/versions`);
      return Array.isArray(data) ? data : [data];
    } catch {
      // Fallback: wrap workspace detail as a single-item version array
      const detail = await safeFetch<any>(`${API_BASE}/api/v1/workspace/story/${storyId}`);
      return [detail].filter(Boolean);
    }
  },

  /** Execution logs for a running story — workspace_routes.py */
  getStoryLogs: (storyId: string) =>
    safeFetch<any>(`${API_BASE}/api/v1/workspace/story/${storyId}/logs`),

  /** Step-by-step execution status — workspace_routes.py (runtime tracking) */
  getStoryStatus: (storyId: string) =>
    safeFetch<any>(`${API_BASE}/api/v1/workspace/story/${storyId}/status`),
};
