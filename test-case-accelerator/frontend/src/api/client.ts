import type { DependencyResponse, DependencyRun, PipelineState, Project, ProjectList, QualityLoop, RuntimeValidationReport, RuntimeValidationRun, SecurityScan, TestGeneration, UnderstandingResponse, VerificationResult, WorkflowResponse } from './types'

const API_BASE = import.meta.env.VITE_API_URL ?? '/api'

export class ApiError extends Error {
  constructor(public status: number, message: string) { super(message) }
}

export function securityScanErrorMessage(reason: unknown): string {
  const message = reason instanceof Error ? reason.message : typeof reason === 'string' ? reason : 'Security scan could not be completed'
  if (/did not return (?:valid )?json|malformed json/i.test(message)) {
    return `${message}. Verify that SEMGREP_CONFIG is an explicit ruleset such as p/default or a valid local rules file/directory; auto requires registry access and metrics.`
  }
  return message
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, init)
  if (!response.ok) {
    let message = `Request failed (${response.status})`
    try { const body = await response.json(); message = body.detail ?? message } catch { /* empty */ }
    throw new ApiError(response.status, typeof message === 'string' ? message : JSON.stringify(message))
  }
  if (response.status === 204) return undefined as T
  return response.json() as Promise<T>
}

async function requestBlob(path: string): Promise<Blob> {
  const response = await fetch(`${API_BASE}${path}`)
  if (!response.ok) {
    let message = `Request failed (${response.status})`
    try { const body = await response.json(); message = typeof body.detail === 'string' ? body.detail : body.detail?.message ?? message } catch { /* empty */ }
    throw new ApiError(response.status, message)
  }
  return response.blob()
}

const json = (body: unknown): RequestInit => ({ method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) })

export const api = {
  health: () => request<Record<string, string>>('/health'),
  projects: (skip = 0, limit = 10) => request<ProjectList>(`/projects?skip=${skip}&limit=${limit}`),
  project: (id: string) => request<Project>(`/projects/${id}`),
  upload: (form: FormData) => request<WorkflowResponse>('/workflows/upload', { method: 'POST', body: form }),
  github: (body: { name: string; description?: string; github_url: string }) => request<WorkflowResponse>('/workflows/github', json(body)),
  uploadProject: (form: FormData) => request<Project>('/projects/upload', { method: 'POST', body: form }),
  githubProject: (body: { name: string; description?: string; github_url: string }) => request<Project>('/projects/github', json(body)),
  deleteProject: (id: string) => request<void>(`/projects/${id}`, { method: 'DELETE' }),
  dependency: (projectId: string) => request<DependencyResponse>(`/projects/${projectId}/dependencies`, { method: 'POST' }),
  securityScan: (projectId: string) => request<SecurityScan>(`/projects/${projectId}/security-scans`, { method: 'POST' }),
  latestSecurityScan: (projectId: string) => request<SecurityScan>(`/projects/${projectId}/security-scan-runs/latest`),
  retrySecurityScan: (runId: string) => request<SecurityScan>(`/security-scan-runs/${runId}/retry`, { method: 'POST' }),
  dependencyRun: (runId: string) => request<DependencyRun>(`/dependency-runs/${runId}`),
  latestDependencyRun: (projectId: string) => request<DependencyRun>(`/projects/${projectId}/dependency-runs/latest`),
  understand: (projectId: string, runId: string) => request<UnderstandingResponse>(`/projects/${projectId}/understand`, json({ dependency_run_id: runId })),
  latestUnderstanding: (projectId: string) => request<UnderstandingResponse>(`/projects/${projectId}/code-understanding-runs/latest`),
  generate: (projectId: string, runId: string) => request<TestGeneration>(`/projects/${projectId}/generate-test-cases`, json({ code_understanding_run_id: runId })),
  latestGeneration: (projectId: string) => request<TestGeneration>(`/projects/${projectId}/generated-test-cases/latest`),
  verify: (projectId: string, runId: string, tests: TestGeneration['generated_test_cases']) => request<VerificationResult>(`/projects/${projectId}/verify-test-cases`, json({ code_understanding_run_id: runId, test_cases: tests })),
  latestVerification: (projectId: string) => request<VerificationResult>(`/projects/${projectId}/verification-results/latest`),
  pipelineState: (projectId: string) => request<PipelineState>(`/projects/${projectId}/pipeline-state`),
  retryPipeline: (runId: string) => request<UnderstandingResponse>(`/pipeline/${runId}/retry`, { method: 'POST' }),
  optimize: (projectId: string, runId: string, tests: TestGeneration['generated_test_cases'], verification: VerificationResult) => request<QualityLoop>(`/projects/${projectId}/optimize-test-quality`, json({ code_understanding_run_id: runId, test_cases: tests, verification })),
  startRuntimeValidation: (projectId: string, runId: string, baseUrl: string) => request<RuntimeValidationRun>(`/projects/${projectId}/runtime-validation`, json({ code_understanding_run_id: runId, base_url: baseUrl })),
  runtimeValidation: (runId: string) => request<RuntimeValidationRun>(`/runtime-validations/${runId}`),
  runtimeValidationReport: (runId: string) => request<RuntimeValidationReport>(`/runtime-validations/${runId}/report`),
  resume: (projectId: string) => request<WorkflowResponse>(`/workflows/${projectId}/resume`, { method: 'POST' }),
  workflowState: (projectId: string) => request<WorkflowResponse>(`/workflows/${projectId}/state`),
  continueWorkflow: (projectId: string, fromStage: 'stage_1' | 'stage_2' | 'stage_3') => request<WorkflowResponse>(`/workflows/${projectId}/continue`, json({ from_stage: fromStage })),
  regenerateFromStage4: (projectId: string) => request<WorkflowResponse>(`/workflows/${projectId}/resume`, json({
    start_stage: 'test_generation',
    force: true,
  })),
  exportTestSuite: (projectId: string) => requestBlob(`/projects/${projectId}/exports/test-suite`),
}
