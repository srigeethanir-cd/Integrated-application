/**
 * Dashboard API — all data-fetching functions consumed by hooks.
 * Presentation-only: no business logic here.
 */

import { get, post } from './apiClient';
import type {
  ApiResponse,
  Project,
  PipelineStatus,
  Epic,
  Story,
  Blueprint,
  Component,
  GeneratedFile,
  ApprovalStatus,
  ApprovalReport,
  GenerationHistoryItem,
  StoryAuditItem,
  ReportSummary,
  DashboardSummary,
} from './types';

// ─── Projects ─────────────────────────────────────────────────────────────────

export const fetchProjects = (skip = 0, limit = 100) =>
  get<ApiResponse<Project[]>>('/projects/', { skip, limit });

export const fetchProject = (id: string) =>
  get<ApiResponse<Project>>(`/projects/${id}`);

// ─── Pipeline status ──────────────────────────────────────────────────────────

export const fetchPipelineStatus = () =>
  get<ApiResponse<PipelineStatus>>('/project/status');

// ─── Epics ────────────────────────────────────────────────────────────────────

export const fetchEpics = (skip = 0, limit = 50) =>
  get<ApiResponse<Epic[]>>('/epics/', { skip, limit });

export const fetchEpic = (id: string) =>
  get<ApiResponse<Epic>>(`/epics/${id}`);

// ─── Stories ─────────────────────────────────────────────────────────────────

export const fetchStories = (params?: { epic_id?: string; status?: string; skip?: number; limit?: number }) =>
  get<ApiResponse<Story[]> | Story[]>('/stories/', params as Record<string, unknown>);

export const fetchStory = (id: string) =>
  get<Story>(`/stories/${id}`);

export const approveStory = (id: string) =>
  post<Story>(`/stories/${id}/approve`);

// ─── Blueprints ───────────────────────────────────────────────────────────────

export const fetchBlueprints = () =>
  get<ApiResponse<Blueprint[]>>('/blueprints/');

// ─── Components ───────────────────────────────────────────────────────────────

export const fetchComponents = () =>
  get<ApiResponse<Component[]>>('/components/');

// ─── Files ───────────────────────────────────────────────────────────────────

export const fetchFiles = (skip = 0, limit = 200) =>
  get<ApiResponse<GeneratedFile[]>>('/files/', { skip, limit });

// ─── Approval ────────────────────────────────────────────────────────────────

export const fetchApprovalStatus = () =>
  get<ApiResponse<ApprovalStatus>>('/approval/status');

export const fetchApprovalHistory = () =>
  get<ApiResponse<import('./types').ApprovalHistoryItem[]>>('/approval/history');

export const fetchApprovalReport = () =>
  get<ApiResponse<ApprovalReport>>('/approval/report');

// ─── Reports / summary ───────────────────────────────────────────────────────

export const fetchReportSummary = () =>
  get<ApiResponse<ReportSummary>>('/reports/summary');

// ─── Activity (generation history + audits) ──────────────────────────────────

export const fetchGenerationHistory = (limit = 20) =>
  get<ApiResponse<GenerationHistoryItem[]>>('/reports/generation-history', { limit });

export const fetchStoryAudits = (limit = 20) =>
  get<ApiResponse<StoryAuditItem[]>>('/reports/story-audits', { limit });

// ─── Aggregated dashboard summary (computed client-side from stories+epics) ──

export async function fetchDashboardSummary(): Promise<DashboardSummary> {
  const [epicsRes, storiesRes, filesRes] = await Promise.allSettled([
    fetchEpics(),
    fetchStories({ limit: 500 }),
    fetchFiles(0, 500),
  ]);

  const epics: Epic[] = epicsRes.status === 'fulfilled'
    ? (epicsRes.value?.data ?? []) as Epic[]
    : [];

  const rawStories = storiesRes.status === 'fulfilled' ? storiesRes.value : null;
  const stories: Story[] = Array.isArray(rawStories)
    ? rawStories
    : (rawStories as ApiResponse<Story[]>)?.data ?? [];

  const files: GeneratedFile[] = filesRes.status === 'fulfilled'
    ? ((filesRes.value as ApiResponse<GeneratedFile[]>)?.data ?? [])
    : [];

  const completed = stories.filter(
    (s) => s.merge_status === 'MERGED' || s.approval_status === 'approved',
  ).length;

  const pendingApproval = stories.filter(
    (s) => s.validation_status === 'VALIDATED' && s.approval_status === 'pending',
  ).length;

  const inProgress = stories.filter(
    (s) => s.generation_status === 'GENERATING',
  ).length;

  const completedPct = stories.length > 0
    ? Math.round((completed / stories.length) * 100)
    : 0;

  return {
    total_epics: epics.length,
    total_stories: stories.length,
    completed_stories: completed,
    pending_approval: pendingApproval,
    in_progress: inProgress,
    generated_files: files.length,
    completed_percentage: completedPct,
  };
}

// ─── Traceability ─────────────────────────────────────────────────────────────

export const fetchTraceabilityMatrix = () =>
  get<ApiResponse<Record<string, unknown>>>('/traceability/matrix');

// ─── Workspace ────────────────────────────────────────────────────────────────

export const fetchWorkspace = () =>
  get<ApiResponse<{ workspace_root: string; folders_count: number; folders: string[] }>>('/project/workspace');

// Re-export ApprovalHistoryItem so it's available from this module
export type { ApprovalHistoryItem } from './types';
