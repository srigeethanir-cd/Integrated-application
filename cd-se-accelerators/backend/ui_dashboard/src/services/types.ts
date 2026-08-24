// ─── Shared API Response Envelope ────────────────────────────────────────────

export interface ApiResponse<T = unknown> {
  success: boolean;
  message: string;
  data: T;
}

// ─── Project ──────────────────────────────────────────────────────────────────

export type ProjectStatus =
  | 'INITIALIZED'
  | 'RUNNING_STAGE_1'
  | 'GENERATING'
  | 'VALIDATION_PENDING'
  | 'VALIDATION_FAILED'
  | 'PAUSED_FOR_HUMAN_APPROVAL'
  | 'REJECTED_BY_BA'
  | 'READY_TO_MERGE'
  | 'PROJECT_VALIDATED'
  | 'EXPORT_READY'
  | 'COMPLETED'
  | 'ACTIVE';

export interface Project {
  id: string;
  name: string;
  description: string | null;
  tech_stack: Record<string, string> | string | null;
  status: ProjectStatus;
  created_at: string;
  updated_at: string;
}

// ─── Pipeline / Workflow Status ───────────────────────────────────────────────

export interface StoryPipelineStatus {
  story_key: string;
  epic_key: string;
  title: string;
  generation_status: string;
  validation_status: string;
  preview_status: string;
  approval_status: string;
  merge_status: string;
  export_status: string;
  version: string;
  retry_count: number;
  assigned_agent: string;
}

export interface PipelineStatus {
  project_name: string;
  progress_percentage: number;
  execution_status: string;
  current_agent: string;
  stories: StoryPipelineStatus[];
  // envelope extras
  action?: string;
  project_id?: string;
  next_agent?: string;
  validation_state?: string;
  retry_count?: number;
  generated_artifact_locations?: Record<string, string>;
}

// ─── Epic ─────────────────────────────────────────────────────────────────────

export interface Epic {
  id: string;
  project_id: string;
  blueprint_id: string;
  epic_key: string;
  title: string;
  description: string | null;
  priority: 'high' | 'medium' | 'low' | null;
  created_at: string;
  // computed / joined fields
  total_stories?: number;
  completed_stories?: number;
  pending_stories?: number;
  progress_percentage?: number;
  status_label?: 'On Track' | 'In Progress' | 'Behind' | 'Completed';
}

// ─── Story ────────────────────────────────────────────────────────────────────

export interface Story {
  id: string;
  story_key: string | null;
  title: string;
  description: string | null;
  acceptance_criteria: Record<string, unknown> | null;
  epic_id: string | null;
  project_id: string | null;
  generation_status: string;
  validation_status: string;
  approval_status: string;
  merge_status: string;
  export_status: string;
  preview_status: string;
  version: number;
  retry_count: number;
  assigned_agent: string;
  created_at: string;
}

// ─── Blueprint ────────────────────────────────────────────────────────────────

export interface Blueprint {
  id: string;
  project_id: string;
  architecture: string | null;
  folder_structure: Record<string, unknown> | null;
  api_design: Record<string, unknown> | null;
  database_design: Record<string, unknown> | null;
  shared_components: Record<string, unknown> | null;
  version: number;
  created_at: string;
}

// ─── Component ────────────────────────────────────────────────────────────────

export interface Component {
  id: string;
  project_id: string;
  name: string;
  type: 'frontend' | 'backend' | 'metadata';
  path: string | null;
  description: string | null;
  created_by_agent: string | null;
  created_at: string;
}

// ─── File ─────────────────────────────────────────────────────────────────────

export interface GeneratedFile {
  id: string;
  component_id: string;
  story_id: string;
  path: string;
  hash: string | null;
  version: number;
  created_at: string;
}

// ─── Approval ─────────────────────────────────────────────────────────────────

export type ApprovalStatusValue = 'PENDING' | 'APPROVED' | 'CHANGES_REQUESTED' | 'REJECTED';

export interface ApprovalStatus {
  status: ApprovalStatusValue;
  reviewer?: string;
  comments?: string;
  timestamp?: string;
}

export interface ApprovalHistoryItem {
  id: string;
  status: ApprovalStatusValue;
  reviewer: string;
  comments: string | null;
  timestamp: string;
}

export interface ApprovalReport {
  readiness_score: number;
  status: ApprovalStatusValue;
  history: ApprovalHistoryItem[];
}

// ─── Generation / Audit Activity ─────────────────────────────────────────────

export type ActivityKind =
  | 'generation'
  | 'approval'
  | 'blueprint'
  | 'merge'
  | 'database'
  | 'validation';

export interface ActivityItem {
  id: string;
  kind: ActivityKind;
  title: string;
  subtitle: string;
  agent?: string;
  story_key?: string;
  timestamp: string;
}

export interface GenerationHistoryItem {
  id: string;
  story_id: string;
  agent: string;
  action: string;
  status: string;
  execution_time: number | null;
  timestamp: string;
}

export interface StoryAuditItem {
  id: string;
  story_id: string;
  user: string;
  agent: string;
  previous_state: string;
  new_state: string;
  comments: string | null;
  timestamp: string;
}

// ─── Reports / Summary ────────────────────────────────────────────────────────

export interface ReportSummary {
  architecture_readiness_score: number;
  approval_gate_status: ApprovalStatusValue;
  traceability_nodes_count: number;
  traceability_edges_count: number;
  system_health: string;
}

// ─── Dashboard aggregated ─────────────────────────────────────────────────────

export interface DashboardSummary {
  total_epics: number;
  total_stories: number;
  completed_stories: number;
  pending_approval: number;
  in_progress: number;
  generated_files: number;
  completed_percentage: number;
}

// ─── Notifications ────────────────────────────────────────────────────────────

export interface Notification {
  id: string;
  type: 'approval' | 'workflow' | 'info' | 'error';
  message: string;
  timestamp: string;
  read: boolean;
}

// ─── WebSocket message ────────────────────────────────────────────────────────

export interface WsMessage {
  type: 'pipeline_update' | 'approval_update' | 'story_update' | 'ping';
  payload: unknown;
}
