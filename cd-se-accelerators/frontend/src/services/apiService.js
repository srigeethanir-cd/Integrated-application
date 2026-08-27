/**
 * API Service for UI TestCase Generator Frontend.
 * Connects directly to FastAPI backend endpoints running on http://localhost:8000.
 */

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

/**
 * Health check probe
 */
export async function checkBackendHealth() {
  try {
    const res = await fetch(`${API_BASE_URL}/`);
    if (!res.ok) return { online: false };
    const data = await res.json();
    return { online: true, ...data };
  } catch (err) {
    return { online: false, error: err.message };
  }
}

/**
 * Upload a frontend project ZIP file
 * POST /source/upload
 */
export async function uploadProjectZip(file) {
  const formData = new FormData();
  formData.append('file', file);

  const res = await fetch(`${API_BASE_URL}/source/upload`, {
    method: 'POST',
    body: formData,
  });

  if (!res.ok) {
    const errData = await res.json().catch(() => ({}));
    throw new Error(errData.detail || `Upload failed with status ${res.status}`);
  }

  return await res.json();
}

/**
 * Detect frontend framework from project path
 * POST /framework/detect
 */
export async function detectFrontendFramework(projectPath) {
  const res = await fetch(`${API_BASE_URL}/framework/detect`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      project_path: projectPath,
    }),
  });

  if (!res.ok) {
    const errData = await res.json().catch(() => ({}));
    throw new Error(errData.detail || `Framework detection failed with status ${res.status}`);
  }

  return await res.json();
}

/**
 * Execute end-to-end or partial backend pipeline execution
 * POST /pipeline/run
 */
export async function runBackendPipelineStage(
  projectPath = 'scratch/test_workspace/react_large',
  runUntil = 'validation',
  pipelineRunId = null,
  projectId = null,
  projectName = null
) {
  try {
    const res = await fetch(`${API_BASE_URL}/pipeline/run`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        project_path: projectPath,
        run_until: runUntil,
        pipeline_run_id: pipelineRunId,
        project_id: projectId,
        project_name: projectName,
        include_timings: true,
        include_intermediate_outputs: true,
      }),
    });

    if (!res.ok) {
      const errData = await res.json().catch(() => ({}));
      throw new Error(errData.detail?.error_message || errData.detail || `Pipeline failed at stage ${runUntil}`);
    }

    return await res.json();
  } catch (err) {
    console.warn(`API Service: Backend stage call '${runUntil}' fallback:`, err.message);
    return {
      status: 'failed',
      failed_stage: runUntil,
      error_message: err.message,
    };
  }
}

/**
 * Trigger real test execution via Jest on stored test files
 * POST /test_execution/run
 */
export async function runTestExecution(pipelineRunId) {
  try {
    const res = await fetch(`${API_BASE_URL}/test_execution/run`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        pipeline_run_id: pipelineRunId,
      }),
    });

    if (!res.ok) {
      const errData = await res.json().catch(() => ({}));
      throw new Error(errData.detail || `Test execution failed with status ${res.status}`);
    }

    return await res.json();
  } catch (err) {
    console.warn('API Service: /test_execution/run endpoint call fallback:', err.message);
    return null;
  }
}

/**
 * Fetch the latest persisted test case plan from backend storage.
 * GET /test_cases/latest
 */
export async function fetchLatestTestCases() {
  try {
    const res = await fetch(`${API_BASE_URL}/test_cases/latest`);
    if (!res.ok) {
      if (res.status === 404) return null; // No stored test cases yet
      return null;
    }
    return await res.json();
  } catch (err) {
    console.warn('API Service: /test_cases/latest fetch failed:', err.message);
    return null;
  }
}

/**
 * Fetch persisted test case plan for a specific pipeline run.
 * GET /test_cases/{pipeline_run_id}
 */
export async function fetchTestCasesByRunId(pipelineRunId) {
  try {
    const res = await fetch(`${API_BASE_URL}/test_cases/${encodeURIComponent(pipelineRunId)}`);
    if (!res.ok) {
      if (res.status === 404) return null;
      return null;
    }
    return await res.json();
  } catch (err) {
    console.warn(`API Service: /test_cases/${pipelineRunId} fetch failed:`, err.message);
    return null;
  }
}

/**
 * Single stage endpoint definitions matching the 9 pipeline stages
 */
export const STAGE_ENDPOINT_MAP = [
  { id: 1, stageKey: 'source_ingestion', name: 'Source Ingestion', endpoint: '/source/upload', percent: 11 },
  { id: 2, stageKey: 'framework_detection', name: 'Framework Detection', endpoint: '/framework/detect', percent: 22 },
  { id: 3, stageKey: 'project_analyzer', name: 'Analyzer', endpoint: '/analyzer/analyze', percent: 33 },
  { id: 4, stageKey: 'ir_generator', name: 'IR Generator', endpoint: '/ir/generate', percent: 44 },
  { id: 5, stageKey: 'strategy_generator', name: 'Strategy Engine', endpoint: '/strategy/generate', percent: 55 },
  { id: 6, stageKey: 'edge_case_generator', name: 'Edge Case Generator', endpoint: '/edge_case/generate', percent: 66 },
  { id: 7, stageKey: 'test_case_generator', name: 'Test Case Generator', endpoint: '/test_case/generate', percent: 77 },
  { id: 8, stageKey: 'test_writer', name: 'Test Writer', endpoint: '/test_writer/generate', percent: 88 },
  { id: 9, stageKey: 'validation', name: 'Validation', endpoint: '/validation/run', percent: 100 },
];

/**
 * Fetch list of all projects from DB
 * GET /projects
 */
export async function fetchProjects() {
  try {
    const res = await fetch(`${API_BASE_URL}/projects`);
    if (!res.ok) return { total_projects: 0, projects: [] };
    return await res.json();
  } catch (err) {
    console.warn('API Service: /projects fetch failed:', err.message);
    return { total_projects: 0, projects: [] };
  }
}

/**
 * Create a project entry in DB
 * POST /projects
 */
export async function createProject(projectData) {
  try {
    const res = await fetch(`${API_BASE_URL}/projects`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(projectData),
    });
    if (!res.ok) throw new Error(`Create project failed: ${res.status}`);
    return await res.json();
  } catch (err) {
    console.warn('API Service: createProject error:', err.message);
    return null;
  }
}

/**
 * Fetch project details by ID
 * GET /projects/{projectId}
 */
export async function fetchProjectDetails(projectId) {
  try {
    const res = await fetch(`${API_BASE_URL}/projects/${encodeURIComponent(projectId)}`);
    if (!res.ok) return null;
    return await res.json();
  } catch (err) {
    console.warn(`API Service: fetchProjectDetails failed for ${projectId}:`, err.message);
    return null;
  }
}

/**
 * Trigger Jest execution for run and save DB report
 * POST /projects/pipeline-runs/{pipelineRunId}/execute
 */
export async function executeRunTests(pipelineRunId) {
  try {
    const res = await fetch(`${API_BASE_URL}/projects/pipeline-runs/${encodeURIComponent(pipelineRunId)}/execute`, {
      method: 'POST',
    });
    if (!res.ok) throw new Error(`Execution failed: ${res.status}`);
    return await res.json();
  } catch (err) {
    console.warn(`API Service: executeRunTests failed for ${pipelineRunId}:`, err.message);
    return null;
  }
}

/**
 * Fetch report for pipeline run
 * GET /projects/pipeline-runs/{pipelineRunId}/report
 */
export async function fetchRunReport(pipelineRunId) {
  try {
    const res = await fetch(`${API_BASE_URL}/projects/pipeline-runs/${encodeURIComponent(pipelineRunId)}/report`);
    if (!res.ok) return null;
    return await res.json();
  } catch (err) {
    console.warn(`API Service: fetchRunReport failed for ${pipelineRunId}:`, err.message);
    return null;
  }
}

/**
 * Fetch test cases for specific project / run
 * GET /projects/{projectId}/test-cases
 */
export async function fetchProjectTestCases(projectId, pipelineRunId = null) {
  try {
    let url = `${API_BASE_URL}/projects/${encodeURIComponent(projectId)}/test-cases`;
    if (pipelineRunId) url += `?pipeline_run_id=${encodeURIComponent(pipelineRunId)}`;
    const res = await fetch(url);
    if (!res.ok) return null;
    return await res.json();
  } catch (err) {
    console.warn(`API Service: fetchProjectTestCases failed for ${projectId}:`, err.message);
    return null;
  }
}

/**
 * Fetch test files for specific project / run
 * GET /projects/{projectId}/test-files
 */
export async function fetchProjectTestFiles(projectId, pipelineRunId = null) {
  try {
    let url = `${API_BASE_URL}/projects/${encodeURIComponent(projectId)}/test-files`;
    if (pipelineRunId) url += `?pipeline_run_id=${encodeURIComponent(pipelineRunId)}`;
    const res = await fetch(url);
    if (!res.ok) return null;
    return await res.json();
  } catch (err) {
    console.warn(`API Service: fetchProjectTestFiles failed for ${projectId}:`, err.message);
    return null;
  }
}

/**
 * Fetch report for a specific project
 * GET /projects/{projectId}/report
 */
export async function fetchProjectReport(projectId) {
  try {
    const res = await fetch(`${API_BASE_URL}/projects/${encodeURIComponent(projectId)}/report`);
    if (!res.ok) return null;
    return await res.json();
  } catch (err) {
    console.warn(`API Service: fetchProjectReport failed for ${projectId}:`, err.message);
    return null;
  }
}

/**
 * Run tests for a specific project
 * POST /projects/{projectId}/run-tests
 */
export async function runProjectTests(projectId) {
  try {
    const res = await fetch(`${API_BASE_URL}/projects/${encodeURIComponent(projectId)}/run-tests`, {
      method: 'POST',
    });
    if (!res.ok) throw new Error(`Execution failed: ${res.status}`);
    return await res.json();
  } catch (err) {
    console.warn(`API Service: runProjectTests failed for ${projectId}:`, err.message);
    return null;
  }
}


