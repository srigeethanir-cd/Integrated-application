/**
 * Story Explorer Dashboard API Service
 * Interacts with real backend workspace data endpoints (backend/workspace/US001...US010)
 */

export interface Story {
  id: string;
  story_id: string;
  title: string;
  description: string;
  status: string;
  epic: string;
  project: string;
  folder_path: string;
  frontend_file_path: string;
  backend_file_path: string;
  frontend_folder_path: string;
  backend_folder_path: string;
  frontend_files: string[];
  backend_files: string[];
  generated_files?: string[];
  frontend_file_count?: number;
  backend_file_count?: number;
  total_file_count?: number;
  validation_score?: number;
  confidence?: number;
  generation_time?: string;
  has_preview?: boolean;
  has_live_preview?: boolean;
  preview_image?: string;
  preview_html?: string;
  preview_image_path?: string;
  live_preview_url?: string;
  acceptance_criteria?: string[];
  created_timestamp?: string;
  updated_timestamp?: string;
  generated_at?: string;
  updated_at?: string;
}

export interface StoryFileContent {
  story_id: string;
  path: string;
  filename: string;
  content: string;
}

export interface ActionResponse {
  success: boolean;
  message: string;
  story_id: string;
  status: string;
}

export interface ValidationSummary {
  files_generated: number;
  frontend_files: number;
  backend_files: number;
  validation_status: string;
  confidence: string;
  story_completion: string;
  total_stories: number;
  approved_stories: number;
  coverage?: string;
  traceability?: string;
  lint_status?: string;
  api_status?: string;
  database_status?: string;
}

export interface MergeStatus {
  status: string;
  merged_count: number;
  merged_files_count?: number;
  last_merge_time?: string;
  log?: string;
  preview_url?: string;
}

export const API_BASE = (import.meta.env && import.meta.env.VITE_API_BASE_URL)
  ? import.meta.env.VITE_API_BASE_URL
  : '/api-code';

async function safeJsonParse(res: Response): Promise<any> {
  if (!res.ok) return null;
  const contentType = res.headers.get('content-type') || '';
  if (!contentType.includes('application/json')) {
    console.warn(`Expected JSON response from ${res.url}, but got ${contentType}`);
    return null;
  }
  try {
    return await res.json();
  } catch (err) {
    console.error(`Failed parsing JSON from ${res.url}:`, err);
    return null;
  }
}

/**
 * Fetch all available user stories dynamically from backend/workspace.
 */
export async function fetchStories(forceRefresh: boolean = false): Promise<Story[]> {
  try {
    const url = `${API_BASE}/api/v1/workspace/stories${forceRefresh ? '?refresh=true' : ''}`;
    const res = await fetch(url);
    if (!res.ok) {
      const resOld = await fetch(`${API_BASE}/api/v1/stories/${forceRefresh ? '?refresh=true' : ''}`);
      const dataOld = await safeJsonParse(resOld);
      return dataOld || [];
    }
    const data = await safeJsonParse(res);
    return data || [];
  } catch (error) {
    console.error('Error fetching stories:', error);
    return [];
  }
}

/**
 * Fetch metadata for a specific story by ID.
 */
export async function fetchStoryById(storyId: string): Promise<Story | null> {
  try {
    const res = await fetch(`${API_BASE}/api/v1/workspace/story/${storyId}`);
    if (!res.ok) {
      const resOld = await fetch(`${API_BASE}/api/v1/stories/${storyId}`);
      if (!resOld.ok) return null;
      return await resOld.json();
    }
    return await res.json();
  } catch (error) {
    console.error(`Error fetching story ${storyId}:`, error);
    return null;
  }
}

/**
 * Fetch metadata.json fields for a specific story.
 */
export async function fetchStoryMetadata(storyId: string): Promise<Record<string, any> | null> {
  try {
    const res = await fetch(`${API_BASE}/api/v1/workspace/story/${storyId}/metadata`);
    if (!res.ok) return null;
    return await res.json();
  } catch (error) {
    console.error(`Error fetching metadata for ${storyId}:`, error);
    return null;
  }
}

/**
 * Get live preview URL for story's preview.html or preview/dist/index.html iframe.
 */
export function getLivePreviewUrl(storyId: string): string {
  return `${API_BASE}/api/v1/workspace/story/${storyId}/live-preview`;
}

/**
 * Check if preview app exists for a story.
 */
export async function fetchPreviewStatus(storyId: string): Promise<any> {
  try {
    const res = await fetch(`${API_BASE}/api/v1/workspace/story/${storyId}/preview/status`);
    if (!res.ok) return null;
    return await res.json();
  } catch (error) {
    console.error(`Error checking preview status for ${storyId}:`, error);
    return null;
  }
}

/**
 * Trigger story preview application launch.
 */
export async function launchStoryPreview(storyId: string): Promise<any> {
  try {
    const res = await fetch(`${API_BASE}/api/v1/workspace/story/${storyId}/launch-preview`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
    });
    if (!res.ok) return null;
    return await res.json();
  } catch (error) {
    console.error(`Error launching story preview for ${storyId}:`, error);
    return null;
  }
}

/**
 * Get static preview.png image URL for story.
 */
export function getStoryPreviewImageUrl(storyId: string): string {
  return `${API_BASE}/api/v1/workspace/story/${storyId}/preview`;
}

/**
 * Fetch aggregated validation summary statistics from backend metadata.
 */
export async function fetchValidationSummary(): Promise<ValidationSummary | null> {
  try {
    const res = await fetch(`${API_BASE}/api/v1/workspace/validation-summary`);
    if (!res.ok) {
      const resOld = await fetch(`${API_BASE}/api/v1/stories/validation-summary`);
      if (!resOld.ok) return null;
      return await resOld.json();
    }
    return await res.json();
  } catch (error) {
    console.error('Error fetching validation summary:', error);
    return null;
  }
}

/**
 * Fetch list of files for a story workspace.
 */
export async function fetchStoryFiles(storyId: string): Promise<{ folder_path: string; files: string[]; generated_files?: string[] }> {
  try {
    const res = await fetch(`${API_BASE}/api/v1/workspace/story/${storyId}/files`);
    if (!res.ok) return { folder_path: 'frontend/', files: [] };
    return await res.json();
  } catch (error) {
    console.error(`Error fetching files for ${storyId}:`, error);
    return { folder_path: 'frontend/', files: [] };
  }
}

/**
 * Load raw code file content for a given story and relative file path.
 */
export async function fetchFileContent(storyId: string, path: string): Promise<string> {
  try {
    const res = await fetch(`${API_BASE}/api/v1/workspace/story/${storyId}/file?path=${encodeURIComponent(path)}`);
    if (!res.ok) {
      const resOld = await fetch(`${API_BASE}/api/v1/workspace/explorer/${storyId}/file?path=${encodeURIComponent(path)}`);
      if (!resOld.ok) return `// File ${path} could not be loaded directly from workspace.`;
      const dataOld = await resOld.json();
      return dataOld.content || dataOld;
    }
    const data: StoryFileContent = await res.json();
    return data.content;
  } catch (error) {
    console.error(`Error loading file ${path}:`, error);
    return `// Error reading file ${path} from workspace.`;
  }
}

/**
 * Post story approval to backend workspace.
 */
export async function approveStory(storyId: string): Promise<ActionResponse> {
  try {
    const res = await fetch(`${API_BASE}/api/v1/stories/${storyId}/approve`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
    });
    if (!res.ok) {
      const resOld = await fetch(`${API_BASE}/api/v1/workspace/story/${storyId}/approve`, { method: 'POST' });
      if (!resOld.ok) throw new Error('Approval endpoint failed');
      return await resOld.json();
    }
    return await res.json();
  } catch (error) {
    console.error(`Error approving story ${storyId}:`, error);
    return {
      success: false,
      message: `Failed to approve story ${storyId}`,
      story_id: storyId,
      status: 'Error'
    };
  }
}

/**
 * Post story rejection to backend workspace.
 */
export async function rejectStory(storyId: string): Promise<ActionResponse> {
  try {
    const res = await fetch(`${API_BASE}/api/v1/stories/${storyId}/reject`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ reason: 'Story rejected by user' }),
    });
    if (!res.ok) {
      const resOld = await fetch(`${API_BASE}/api/v1/workspace/story/${storyId}/reject`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ reason: 'Story rejected by user' }),
      });
      if (!resOld.ok) throw new Error('Rejection endpoint failed');
      return await resOld.json();
    }
    return await res.json();
  } catch (error) {
    console.error(`Error rejecting story ${storyId}:`, error);
    return {
      success: false,
      message: `Failed to reject story ${storyId}`,
      story_id: storyId,
      status: 'Error'
    };
  }
}

/**
 * Post story regeneration request to backend workspace.
 */
export async function regenerateStory(storyId: string): Promise<ActionResponse> {
  try {
    const res = await fetch(`${API_BASE}/api/v1/stories/${storyId}/regenerate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ refinement_prompt: 'Regenerate user story' }),
    });
    if (!res.ok) {
      const resOld = await fetch(`${API_BASE}/api/v1/workspace/story/${storyId}/regenerate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ refinement_prompt: 'Regenerate user story' }),
      });
      if (!resOld.ok) throw new Error('Regeneration endpoint failed');
      return await resOld.json();
    }
    return await res.json();
  } catch (error) {
    console.error(`Error regenerating story ${storyId}:`, error);
    return {
      success: false,
      message: `Failed to trigger regeneration for ${storyId}`,
      story_id: storyId,
      status: 'Error'
    };
  }
}

/**
 * Trigger Agent-3 integration merge for all approved stories into backend/integrated_project.
 */
export async function triggerMergeIntegrated(): Promise<{ success: boolean; message: string; details?: MergeStatus }> {
  try {
    const res = await fetch(`${API_BASE}/api/v1/workspace/merge`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
    });
    if (!res.ok) {
      const resOld = await fetch(`${API_BASE}/api/v1/project/integrate`, { method: 'POST' });
      if (!resOld.ok) throw new Error('Merge request failed');
      return await resOld.json();
    }
    return await res.json();
  } catch (error: any) {
    console.error('Error merging integrated project:', error);
    return {
      success: false,
      message: error.message || 'Merge operation failed'
    };
  }
}

/**
 * Fetch status of the integrated application build & server launch.
 */
export async function fetchMergeStatus(): Promise<MergeStatus | null> {
  try {
    const res = await fetch(`${API_BASE}/api/v1/workspace/merge/status`);
    if (!res.ok) {
      return null;
    }
    return await res.json();
  } catch (error) {
    console.error('Error fetching merge status:', error);
    return null;
  }
}

export interface ProjectConfig {
  id?: string;
  name: string;
  description: string;
  tech_stack: string | Record<string, any>;
  status?: string;
}

export async function fetchProjectConfig(): Promise<ProjectConfig | null> {
  try {
    const res = await fetch(`${API_BASE}/api/v1/projects`);
    if (!res.ok) return null;
    const result = await res.json();
    const data = result.data || result;
    if (Array.isArray(data) && data.length > 0) {
      return data[0];
    }
    return null;
  } catch (error) {
    console.error('Error fetching project config:', error);
    return null;
  }
}

export async function createProjectConfig(payload: { name: string; description: string; tech_stack: string }): Promise<ProjectConfig | null> {
  try {
    const res = await fetch(`${API_BASE}/api/v1/projects`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    if (!res.ok) throw new Error('Failed to create project configuration');
    const result = await res.json();
    return result.data || result;
  } catch (error) {
    console.error('Error creating project config:', error);
    throw error;
  }
}

export async function updateProjectConfig(id: string, payload: { name: string; description: string; tech_stack: string }): Promise<ProjectConfig | null> {
  try {
    const res = await fetch(`${API_BASE}/api/v1/projects/${id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    if (!res.ok) throw new Error('Failed to update project configuration');
    const result = await res.json();
    return result.data || result;
  } catch (error) {
    console.error('Error updating project config:', error);
    throw error;
  }
}

export async function uploadUserStories(filename: string, stories: any[]): Promise<boolean> {
  try {
    // Correct backend route: /api/v1/documents/upload-user-stories
    const res = await fetch(`${API_BASE}/api/v1/documents/upload-user-stories`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ filename, stories }),
    });
    return res.ok;
  } catch (error) {
    console.error('Error uploading user stories:', error);
    return false;
  }
}

export async function uploadWireframe(filename: string): Promise<boolean> {
  try {
    // Correct backend route: /api/v1/documents/upload-wireframe
    const res = await fetch(`${API_BASE}/api/v1/documents/upload-wireframe`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ filename }),
    });
    return res.ok;
  } catch (error) {
    console.error('Error uploading wireframe:', error);
    return false;
  }
}

export interface GenerateBlueprintPayload {
  project_name: string;
  project_description: string;
  tech_stack: {
    frontend: boolean;
    backend: boolean;
    database: boolean;
    orm: boolean;
  } | string;
  user_stories?: any[];
  wireframe_images?: string[];
  workspace_metadata?: any;
}

export async function generateAgent1Blueprint(payload: GenerateBlueprintPayload): Promise<any> {
  try {
    // Primary: POST /api/v1/agents/agent1/run
    const res = await fetch(`${API_BASE}/api/v1/agents/agent1/run`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    if (!res.ok) {
      // Fallback: POST /api/v1/project/run (end-to-end workflow route)
      const resAlt = await fetch(`${API_BASE}/api/v1/project/run`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });
      if (!resAlt.ok) {
        const errorData = await resAlt.json().catch(() => null);
        throw new Error(errorData?.detail || errorData?.message || `Blueprint generation failed with status ${resAlt.status}`);
      }
      const dataAlt = await resAlt.json();
      return dataAlt.data || dataAlt;
    }
    const data = await res.json();
    return data.data || data;
  } catch (error: any) {
    console.error('Error in generateAgent1Blueprint:', error);
    throw error;
  }
}

/**
 * Run Agent-2 code generation for a single story.
 * Uses the real active project_id (not a hardcoded constant).
 */
export async function runAgent2Story(storyKey: string, storyObj?: any, projectId?: string): Promise<any> {
  try {
    const payload = {
      story_key: storyKey,
      story: storyObj || { story_key: storyKey, title: `User Story ${storyKey}` },
      // Use caller-supplied project_id or active project in storage
      project_id: projectId || (typeof window !== 'undefined' ? localStorage.getItem('active_project_id') : null) || undefined,
    };

    // Primary route: POST /api/v1/agents/agent2/run
    let res = await fetch(`${API_BASE}/api/v1/agents/agent2/run`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });

    if (!res.ok) {
      // Fallback route: POST /api/v1/agent2/run (agent2_routes.py)
      res = await fetch(`${API_BASE}/api/v1/agent2/run`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
    }

    if (!res.ok) {
      throw new Error(`Agent-2 execution failed for ${storyKey} (status ${res.status})`);
    }

    const data = await res.json();
    return data.data || data;
  } catch (error: any) {
    console.error(`Error in runAgent2Story for ${storyKey}:`, error);
    throw error;
  }
}


// ═══════════════════════════════════════════════════════════════════════════
// TodoApp Workspace API Functions (Live Generation)
// ═══════════════════════════════════════════════════════════════════════════

/**
 * Start Agent-2 background pipeline for TodoApp (US001..US010).
 * Route: POST /api/v1/agent2/start
 */
export async function startAgent2Pipeline(): Promise<any> {
  try {
    const res = await fetch(`${API_BASE}/api/v1/agent2/start`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
    });
    if (!res.ok) throw new Error(`Failed to start Agent-2 pipeline (status ${res.status})`);
    return await res.json();
  } catch (error: any) {
    console.error('Error starting Agent-2 pipeline:', error);
    throw error;
  }
}

/**
 * Fetch TodoApp project metadata from workspace.
 */
export async function fetchTodoAppProject(): Promise<any> {
  try {
    const res = await fetch(`${API_BASE}/api/v1/workspace/projects/TodoApp`);
    if (!res.ok) return null;
    return await res.json();
  } catch (error) {
    console.error('Error fetching TodoApp project:', error);
    return null;
  }
}

/**
 * Fetch all TodoApp stories from workspace.
 */
export async function fetchTodoAppStories(): Promise<Story[]> {
  try {
    const res = await fetch(`${API_BASE}/api/v1/workspace/projects/TodoApp/stories`);
    if (!res.ok) return [];
    const data = await res.json();
    return Array.isArray(data) ? data : [];
  } catch (error) {
    console.error('Error fetching TodoApp stories:', error);
    return [];
  }
}

/**
 * Fetch execution logs for a specific story.
 */
export async function fetchStoryLogs(storyId: string): Promise<string[]> {
  try {
    const res = await fetch(`${API_BASE}/api/v1/workspace/story/${storyId}/logs`);
    if (!res.ok) return [];
    const data = await res.json();
    return data.logs || [];
  } catch (error) {
    console.error(`Error fetching logs for ${storyId}:`, error);
    return [];
  }
}

/**
 * Fetch step-by-step execution status for a specific story.
 */
export async function fetchStoryStatus(storyId: string): Promise<any> {
  try {
    const res = await fetch(`${API_BASE}/api/v1/workspace/story/${storyId}/status`);
    if (!res.ok) return null;
    return await res.json();
  } catch (error) {
    console.error(`Error fetching status for ${storyId}:`, error);
    return null;
  }
}

// ═══════════════════════════════════════════════════════════════════════════
// Integrated Application Runner API Functions
// ═══════════════════════════════════════════════════════════════════════════

export async function startIntegratedProject(projectPath?: string): Promise<any> {
  try {
    const res = await fetch(`${API_BASE}/api/v1/integrated-project/start`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ project_path: projectPath }),
    });
    if (!res.ok) throw new Error('Failed to start integrated application');
    const json = await res.json();
    return json.data || json;
  } catch (error) {
    console.error('Error starting integrated application:', error);
    throw error;
  }
}

export async function stopIntegratedProject(): Promise<any> {
  try {
    const res = await fetch(`${API_BASE}/api/v1/integrated-project/stop`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
    });
    if (!res.ok) throw new Error('Failed to stop integrated application');
    const json = await res.json();
    return json.data || json;
  } catch (error) {
    console.error('Error stopping integrated application:', error);
    throw error;
  }
}

export async function getIntegratedProjectStatus(): Promise<any> {
  try {
    const res = await fetch(`${API_BASE}/api/v1/integrated-project/status`);
    if (!res.ok) return null;
    const json = await res.json();
    return json.data || json;
  } catch (error) {
    console.error('Error fetching integrated application status:', error);
    return null;
  }
}

export async function getIntegratedProjectLogs(limit = 100): Promise<{ logs: string[]; status: string; is_healthy: boolean }> {
  try {
    const res = await fetch(`${API_BASE}/api/v1/integrated-project/logs?limit=${limit}`);
    if (!res.ok) return { logs: [], status: 'stopped', is_healthy: false };
    const json = await res.json();
    return json.data || { logs: [], status: 'stopped', is_healthy: false };
  } catch (error) {
    console.error('Error fetching integrated application logs:', error);
    return { logs: [], status: 'stopped', is_healthy: false };
  }
}

/**
 * Fetch the story workspace explorer structure, including folder tree and metadata.
 */
export async function fetchStoryExplorer(storyId: string): Promise<any> {
  try {
    const res = await fetch(`${API_BASE}/api/v1/workspace/explorer/${storyId}`);
    if (!res.ok) return null;
    const json = await res.json();
    return json.data || json;
  } catch (error) {
    console.error(`Error fetching explorer structure for story ${storyId}:`, error);
    return null;
  }
}

/**
 * Fetch raw file content for a story file using the workspace explorer route.
 */
export async function fetchStoryExplorerFile(storyId: string, path: string): Promise<any> {
  try {
    const res = await fetch(`${API_BASE}/api/v1/workspace/explorer/${storyId}/file?path=${encodeURIComponent(path)}`);
    if (!res.ok) return null;
    const json = await res.json();
    return json.data || json;
  } catch (error) {
    console.error(`Error loading workspace file ${path} for story ${storyId}:`, error);
    return null;
  }
}

/**
 * Fetch endpoints decorators identified in backend for the user story.
 */
export async function fetchStoryExplorerApis(storyId: string): Promise<any> {
  try {
    const res = await fetch(`${API_BASE}/api/v1/workspace/explorer/${storyId}/apis`);
    if (!res.ok) return null;
    const json = await res.json();
    return json.data || json;
  } catch (error) {
    console.error(`Error loading API mappings for story ${storyId}:`, error);
    return null;
  }
}

/**
 * Fetch the 9-layer project traceability matrix.
 */
export async function fetchTraceabilityMatrix(): Promise<any> {
  try {
    const res = await fetch(`${API_BASE}/api/v1/project/traceability`);
    if (!res.ok) {
      const resOld = await fetch(`${API_BASE}/api/v1/traceability/matrix`);
      if (!resOld.ok) return null;
      const jsonOld = await resOld.json();
      return jsonOld.data || jsonOld;
    }
    const json = await res.json();
    return json.data || json;
  } catch (error) {
    console.error('Error fetching traceability matrix:', error);
    return null;
  }
}
