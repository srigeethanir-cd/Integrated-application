/**
 * Domain-level hooks that wrap useApi for every dashboard section.
 * Components import these hooks — never call API functions directly.
 */

import { useMemo } from 'react';
import { useApi } from './useApi';
import type { UseApiState } from './useApi';
import {
  fetchPipelineStatus,
  fetchProjects,
  fetchEpics,
  fetchStories,
  fetchDashboardSummary,
  fetchReportSummary,
  fetchApprovalStatus,
  fetchApprovalHistory,
  fetchGenerationHistory,
  fetchStoryAudits,
  fetchFiles,
  fetchComponents,
} from '@/services/dashboardApi';
import type {
  PipelineStatus,
  Project,
  Epic,
  Story,
  DashboardSummary,
  ReportSummary,
  ApprovalStatus,
  GenerationHistoryItem,
  StoryAuditItem,
  GeneratedFile,
  Component,
  ActivityItem,
  ActivityKind,
} from '@/services/types';
import type { ApiResponse } from '@/services/types';
import type { ApprovalHistoryItem } from '@/services/dashboardApi';

// ─── Pipeline status (polled every 5 s) ──────────────────────────────────────

export function usePipelineStatus(): UseApiState<PipelineStatus> {
  const raw = useApi(
    () => fetchPipelineStatus().then((r) => r.data),
    [],
    { pollingMs: 5_000 },
  );
  return raw;
}

// ─── Projects ─────────────────────────────────────────────────────────────────

export function useProjects(): UseApiState<Project[]> {
  return useApi(
    () => fetchProjects().then((r) => r.data),
    [],
    { pollingMs: 15_000 },
  );
}

// ─── Epics ────────────────────────────────────────────────────────────────────

export function useEpics(): UseApiState<Epic[]> {
  return useApi(
    () => fetchEpics().then((r) => r.data),
    [],
    { pollingMs: 10_000 },
  );
}

// ─── Stories ─────────────────────────────────────────────────────────────────

export function useStories(epicId?: string): UseApiState<Story[]> {
  return useApi(
    () =>
      fetchStories({ epic_id: epicId, limit: 500 }).then((res) =>
        Array.isArray(res) ? res : (res as ApiResponse<Story[]>).data,
      ),
    [epicId],
    { pollingMs: 10_000 },
  );
}

// ─── Dashboard aggregated summary ────────────────────────────────────────────

export function useDashboardSummary(): UseApiState<DashboardSummary> {
  return useApi(fetchDashboardSummary, [], { pollingMs: 10_000 });
}

// ─── Report summary ──────────────────────────────────────────────────────────

export function useReportSummary(): UseApiState<ReportSummary> {
  return useApi(
    () => fetchReportSummary().then((r) => r.data),
    [],
    { pollingMs: 30_000 },
  );
}

// ─── Approval ────────────────────────────────────────────────────────────────

export function useApprovalStatus(): UseApiState<ApprovalStatus> {
  return useApi(
    () => fetchApprovalStatus().then((r) => r.data),
    [],
    { pollingMs: 5_000 },
  );
}

export function useApprovalHistory(): UseApiState<ApprovalHistoryItem[]> {
  return useApi(
    () => fetchApprovalHistory().then((r) => r.data),
    [],
    { pollingMs: 15_000 },
  );
}

// ─── Files ───────────────────────────────────────────────────────────────────

export function useGeneratedFiles(): UseApiState<GeneratedFile[]> {
  return useApi(
    () => fetchFiles().then((r) => (r as ApiResponse<GeneratedFile[]>).data),
    [],
    { pollingMs: 15_000 },
  );
}

// ─── Components ───────────────────────────────────────────────────────────────

export function useComponents(): UseApiState<Component[]> {
  return useApi(
    () => fetchComponents().then((r) => (r as ApiResponse<Component[]>).data),
    [],
    { pollingMs: 30_000 },
  );
}

// ─── Recent Activity — merged + sorted ───────────────────────────────────────

const KIND_MAP: Record<string, ActivityKind> = {
  generate_story_code:       'generation',
  integrate_and_validate:    'merge',
  approval_requested:        'approval',
  blueprint_created:         'blueprint',
  database_schema_updated:   'database',
  validation_passed:         'validation',
};

function mapGenerationToActivity(item: GenerationHistoryItem): ActivityItem {
  const action = item.action ?? '';
  const kind: ActivityKind = KIND_MAP[action] ?? 'generation';

  const agentLabel = item.agent ?? 'Agent';
  const actionLabel =
    action === 'generate_story_code'
      ? 'completed generation'
      : action === 'integrate_and_validate'
      ? 'merged to integration'
      : action.replace(/_/g, ' ');

  return {
    id:        item.id,
    kind,
    title:     `${agentLabel} ${actionLabel}`,
    subtitle:  item.status === 'completed' ? 'Completed successfully' : item.status,
    agent:     item.agent,
    timestamp: item.timestamp,
  };
}

function mapAuditToActivity(item: StoryAuditItem): ActivityItem {
  const stateLabel = item.new_state ?? '';
  let kind: ActivityKind = 'generation';
  if (stateLabel.toLowerCase().includes('approv')) kind = 'approval';
  else if (stateLabel.toLowerCase().includes('merg'))  kind = 'merge';
  else if (stateLabel.toLowerCase().includes('valid'))  kind = 'validation';

  return {
    id:        item.id,
    kind,
    title:     item.comments ?? `State changed to ${stateLabel}`,
    subtitle:  `${item.previous_state} → ${stateLabel}`,
    agent:     item.agent,
    timestamp: item.timestamp,
  };
}

export function useRecentActivity(): UseApiState<ActivityItem[]> {
  const genState   = useApi(
    () => fetchGenerationHistory(15).then((r) => r.data),
    [],
    { pollingMs: 8_000 },
  );
  const auditState = useApi(
    () => fetchStoryAudits(10).then((r) => r.data),
    [],
    { pollingMs: 8_000 },
  );

  const merged = useMemo<ActivityItem[] | null>(() => {
    if (!genState.data && !auditState.data) return null;
    const genItems   = (genState.data   ?? []).map(mapGenerationToActivity);
    const auditItems = (auditState.data ?? []).map(mapAuditToActivity);
    return [...genItems, ...auditItems]
      .sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime())
      .slice(0, 10);
  }, [genState.data, auditState.data]);

  return {
    data:    merged,
    loading: genState.loading || auditState.loading,
    error:   genState.error ?? auditState.error,
    refetch: () => { genState.refetch(); auditState.refetch(); },
  };
}

// ─── Epics enriched with story counts ────────────────────────────────────────

export function useEnrichedEpics() {
  const epicsState   = useEpics();
  const storiesState = useStories();

  const enriched = useMemo<Epic[] | null>(() => {
    if (!epicsState.data) return null;
    const stories = storiesState.data ?? [];

    return epicsState.data.map((epic) => {
      const epicStories = stories.filter((s) => s.epic_id === epic.id);
      const total       = epicStories.length;
      const completed   = epicStories.filter(
        (s) => s.merge_status === 'MERGED' || s.approval_status === 'approved',
      ).length;
      const pending = epicStories.filter(
        (s) => s.approval_status === 'pending' && s.generation_status !== 'GENERATING',
      ).length;
      const inProg = epicStories.filter((s) => s.generation_status === 'GENERATING').length;
      const pct    = total > 0 ? Math.round((completed / total) * 100) : 0;

      let statusLabel: Epic['status_label'] = 'On Track';
      if (pct === 100)         statusLabel = 'Completed';
      else if (pct >= 60)      statusLabel = 'In Progress';
      else if (pending > 0)    statusLabel = 'In Progress';
      else if (inProg > 0)     statusLabel = 'In Progress';

      // Mark as "Behind" if epic has low completion and > 2 pending
      if (pct < 40 && pending >= 2) statusLabel = 'Behind';

      return {
        ...epic,
        total_stories:       total,
        completed_stories:   completed,
        pending_stories:     pending,
        progress_percentage: pct,
        status_label:        statusLabel,
      };
    });
  }, [epicsState.data, storiesState.data]);

  return {
    data:    enriched,
    loading: epicsState.loading || storiesState.loading,
    error:   epicsState.error ?? storiesState.error,
    refetch: () => { epicsState.refetch(); storiesState.refetch(); },
  };
}
