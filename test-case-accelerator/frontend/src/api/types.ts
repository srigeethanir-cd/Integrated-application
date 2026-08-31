export type ProjectStatus = 'UPLOADED' | 'PROCESSING' | 'READY' | 'FAILED'
export type SourceType = 'ZIP' | 'GITHUB'

export interface Project {
  id: string
  name: string
  description: string | null
  source_type: SourceType
  github_url: string | null
  storage_path: string
  status: ProjectStatus
  created_at: string
  updated_at: string
  ingestion_metadata?: Record<string, unknown> | null
}

export interface ProjectList { items: Project[]; total: number }
export interface DependencyResponse { run_id: string; status: string }
export interface FileMetadata {
  path: string; language: string; is_entry_point: boolean
  imports: string[]; classes: string[]; functions: string[]
}
export interface DependencyRun extends DependencyResponse {
  project_id: string; project_path: string; files: FileMetadata[]
  analysis?: Record<string, unknown>
}
export interface SecurityFinding {
    id: string; rule_id: string; severity: string; cwe: string[]; owasp: string[]
    file: string; line: number; start_line: number; end_line: number
    confidence?: string | null; category?: string | null; code_snippet?: string | null
    message: string; recommendation?: string | null; references: string[]
    duplicate_count: number
  metadata: Record<string, unknown>
}
export interface SecurityScanDiagnostic {
  level: string; category: string; type: string; message: string; path: string | null
}
export interface SecurityScan {
  run_id: string; project_id: string; status: string
  progress_percent: number
  summary: {
    total_findings: number; by_severity: Record<string, number>; files_scanned: number
    errors: number; warnings: number; informational: number; parser_errors: number
    unsupported_files: number; skipped_files: number; skipped_by_reason: Record<string, number>
    diagnostics: SecurityScanDiagnostic[]; engine: string; engine_version?: string | null
    duration_ms?: number | null
    rules_executed?: number | null
      raw_semgrep_json?: Record<string, unknown> | null
      security_score?: number | null
      security_context?: Record<string, unknown>
  } | null
  error_message: string | null; retry_count: number
  created_at: string; started_at: string | null; finished_at: string | null
  findings: SecurityFinding[]
}

export interface ApiEndpoint {
  method: string; route: string; handler: string; file: string
  request_type?: string | null; response_type?: string | null
  request_model?: string | null; response_model?: string | null
  authentication?: string | null; side_effects?: string[]
}
export interface Stage3Result {
  project_summary: string; architecture: string
  modules?: Array<Record<string, unknown>>
  imports?: Array<Record<string, unknown>>
  functions?: Array<Record<string, unknown>>
  classes?: Array<Record<string, unknown>>
  symbol_table?: Array<Record<string, unknown>>
  call_graph?: Array<Record<string, unknown>>
  dependency_graph?: Array<Record<string, unknown>>
  repository_behavior?: Record<string, unknown> | null
  security_findings?: Array<Record<string, unknown>>
  components: Array<Record<string, unknown>>
  entrypoints: Array<Record<string, unknown>>
  api_endpoints: ApiEndpoint[]
  data_models: Array<Record<string, unknown>>
  business_rules: Array<Record<string, unknown>>
  execution_flows: Array<Record<string, unknown>>
  external_dependencies: string[]
  test_targets: Array<Record<string, unknown>>
  ambiguities: Array<Record<string, unknown>>
  analyzed_files: Array<Record<string, unknown>>
  test_generation?: TestGeneration
  test_verification?: VerificationResult
  quality_evaluation?: QualityEvaluation
  quality_optimization?: QualityLoop
}
export interface UnderstandingResponse {
  run_id: string; status: string; result: Stage3Result | null
  failed_stage?: string | null; failure_reason?: string | null
  retry_count?: number; last_successful_stage?: string | null
}

export interface PipelineState {
  project_id: string
  security_scan: SecurityScan | null
  dependency: DependencyRun | null
  understanding: UnderstandingResponse | null
  generation: TestGeneration | null
  verification: VerificationResult | null
  quality: QualityLoop | null
  runtime_preparation?: Record<string, unknown> | null
  failed_stage?: string | null
  failure_reason?: string | null
  retry_count?: number
  last_successful_stage?: string | null
  resumed_stage?: string | null
}

export interface TestCase {
  id: string; title: string; description: string; category: string
  priority: string; severity: string; preconditions: string[]; steps: string[]
  expected_results: string[]; requirement_ids: string[]; business_rule_ids: string[]
  traceability?: Record<string, unknown> | null
  unit_test?: {
    module: string; symbol: string; file: string; is_async: boolean
    parameters: string[]; fixture_names: string[]; patches: string[]
    arguments: Record<string, unknown>; expected_exception?: string | null
    generated_code: string
  } | null
}
export interface TestGeneration {
  generated_test_cases: TestCase[]
  coverage_summary: Record<string, number>
    total_generated: number; total_after_deduplication: number
    generation_status?: 'complete' | 'partial_coverage_incomplete'
    generation_reason?: string | null
    uncovered_requirements?: Array<Record<string, string>>
  }
export interface Evidence { file: string; symbol?: string | null; line?: number | null; detail: string }
export interface Finding { check: string; status: 'Verified' | 'Partial' | 'Failed'; detail: string; evidence: Evidence[] }
export interface VerificationItem {
  test_case_id: string; status: 'Verified' | 'Partial' | 'Failed'
  confidence: number; verification_path?: 'Rule-Based' | 'Rule+LLM'; evidence: Evidence[]; findings: Finding[]
}
export interface VerificationResult {
  results: VerificationItem[]
  summary: { verified: number; partial: number; failed: number }
  total_verified: number
}
export interface DimensionScores { [key: string]: number }
export interface RegenerationAction { action: 'ADD' | 'UPDATE' | 'REMOVE'; test_case_id?: string | null; category?: string | null }
export interface RegenerationPlan {
  current_score: number; threshold: number; missing_categories: string[]
  weak_test_cases: string[]; failed_test_cases: string[]
  actions: RegenerationAction[]; rationale: string[]
}
export interface QualityEvaluation {
  overall_score: number; dimension_scores: DimensionScores
  recommendations: string[]; threshold_met: boolean; iteration: number
  regeneration_plan?: RegenerationPlan | null
  feedback: Record<string, unknown>
}
export interface QualityLoop {
  test_generation: TestGeneration; test_verification: VerificationResult
  quality_evaluation: QualityEvaluation; iterations: number
  optimized_test_cases: TestCase[]; evaluation_history: QualityEvaluation[]
  iteration_summaries: Array<{ iteration: number; overall_score: number; verified: number; partial: number; failed: number; preserved: number; regenerated: number; threshold_met: boolean }>
  improvement_metrics: { initial_score: number; final_score: number; score_delta: number; initial_verified: number; final_verified: number; verified_delta: number }
  stopping_reason: string; initial_score: number; final_score: number
  regeneration_plans: RegenerationPlan[]; optimized_test_suite: TestCase[]
  processing_status?: 'completed' | 'partial_success' | 'in_progress'
  resume_point?: string
  final_exit_reason?: string
}

export type RuntimeValidationStatus = 'pending' | 'running' | 'completed' | 'partial' | 'failed' | 'timed_out' | 'cancelled'
export type RuntimeTestStatus = 'Passed' | 'Failed' | 'Skipped' | 'NotExecutable'

export interface RuntimeValidationRun {
  run_id: string
  project_id: string
  source_stage_run_id: string
  status: RuntimeValidationStatus
  execution_mode: string
  base_url: string
  duration_ms: number | null
  summary: RuntimeValidationSummary | null
  error_message: string | null
  created_at: string
  started_at: string | null
  finished_at: string | null
}

export interface RuntimeValidationSummary {
  passed: number
  failed: number
  skipped: number
  not_executable: number
  total: number
  pass_rate: number
  quality_percent?: number
  test_quality_score?: number
  developer_code_issues?: number
  test_infrastructure_issues?: number
  test_generation_issues?: number
}

export interface RuntimeExecutionResult {
  test_case_id: string
  runtime_status: RuntimeTestStatus
  expected_result: Record<string, unknown> | null
  actual_result: Record<string, unknown> | null
  assertion_failure: string | null
  failure_category?: string | null
  developer_action?: string | null
  suggested_fix?: string | null
  logs: string | null
  execution_time_ms: number
}

export interface RuntimeValidationReport {
  run_id: string
  project_id: string
  source_stage_run_id: string
  status: RuntimeValidationStatus
  summary: RuntimeValidationSummary
  pass_rate: number
  duration_ms: number
  failed_tests: string[]
  skipped_tests: string[]
  results: RuntimeExecutionResult[]
}

export interface WorkflowResponse {
  project: Project
  current_stage: 'stage_1' | 'stage_2' | 'stage_3' | 'stage_4'
  status: 'running' | 'completed' | 'waiting_for_approval' | 'failed'
  completed_stage: 'stage_1' | 'stage_2' | 'stage_3' | 'stage_4' | null
  next_stage: 'stage_1' | 'stage_2' | 'stage_3' | 'stage_4' | null
  security_scan: SecurityScan | null
  dependency: DependencyRun | null
  pipeline: UnderstandingResponse | null
  generation: TestGeneration | null
  error: string | null
  logs: string[]
}
