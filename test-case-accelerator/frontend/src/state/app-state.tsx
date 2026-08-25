import { createContext, useContext, useEffect, useMemo, useRef, useState, type ReactNode } from 'react'
import { api, securityScanErrorMessage } from '../api/client'
import type { DependencyRun, Project, QualityLoop, SecurityScan, TestGeneration, UnderstandingResponse, VerificationResult, PipelineState, WorkflowResponse } from '../api/types'

export interface Artifacts {
  securityScan?: SecurityScan
  dependency?: DependencyRun
  understanding?: UnderstandingResponse
  generation?: TestGeneration
  verification?: VerificationResult
  quality?: QualityLoop
  runtimePreparation?: Record<string, unknown>
}

export type UploadMode = 'zip' | 'github'
export type WorkflowMode = 'quick' | 'review'
export type JobStatus = 'running' | 'paused' | 'complete' | 'failed'
export interface JobActivity {
  id: string
  label: string
  detail: string
  at: Date
  status: 'complete' | 'active' | 'failed'
}
export interface PipelineJob {
  projectId: string
  projectName: string
  stage: string
  progress: number
  status: JobStatus
  estimatedTime: string
  iteration: number
  retryAttempt?: number
  resumedStage?: string
  kind: 'security_scan' | 'pipeline'
  completionPath: string
  timeline: JobActivity[]
  error?: string
  pausedAfterStage3?: boolean
  currentStage?: 'stage_1' | 'stage_2' | 'stage_3' | 'stage_4' | 'stage_5' | 'stage_6' | 'stage_7'
  nextStage?: 'stage_1' | 'stage_2' | 'stage_3' | 'stage_4' | null
  logs?: string[]
}

interface Activity { id: string; label: string; detail: string; at: Date }
interface AppState {
  projects: Project[]; setProjects: (value: Project[]) => void
  refreshProjects: () => Promise<void>; removeProject: (id: string) => void
  activeProjectId: string; setActiveProjectId: (value: string) => void
  artifacts: Artifacts; setArtifacts: (value: Artifacts | ((current: Artifacts) => Artifacts)) => void
  artifactsLoading: boolean
  refreshProjectArtifacts: (projectId: string) => Promise<void>
  activities: Activity[]; record: (label: string, detail: string) => void
  uploadMode: UploadMode | null; openUpload: (mode: UploadMode) => void; closeUpload: () => void
  jobs: Record<string, PipelineJob>; startSecurityScan: (project: Project) => void; retrySecurityScan: (project: Project) => void; startPipeline: (project: Project) => void; resumePipeline: (project: Project) => void
  developerMode: (projectId: string) => boolean
  setDeveloperMode: (projectId: string, enabled: boolean) => void
  continuePipeline: (project: Project) => void
  beginApprovalWorkflow: (workflow: WorkflowResponse, mode?: WorkflowMode) => void
  startQuickWorkflow: (project: Project) => void
  continueAfterSecurity: (project: Project) => void
  approveNextStage: (project: Project) => void
  workflowMode: (projectId: string) => WorkflowMode
}

function approvalJob(workflow: WorkflowResponse): PipelineJob {
  const progress = { stage_1: 15, stage_2: 30, stage_3: 45, stage_4: 60 }[workflow.current_stage]
  const label = { stage_1: 'Project setup', stage_2: 'Repository and security analysis', stage_3: 'Test target analysis', stage_4: 'Unit test generation' }[workflow.current_stage]
  return {
    projectId: workflow.project.id,
    projectName: workflow.project.name,
    stage: workflow.status === 'failed' ? `${label} failed` : workflow.status === 'waiting_for_approval' ? `${label} ready for review` : `Running ${label}`,
    progress,
    status: workflow.status === 'failed' ? 'failed' : workflow.status === 'waiting_for_approval' ? 'paused' : 'running',
    estimatedTime: workflow.status === 'waiting_for_approval' ? 'Waiting for approval' : 'In progress',
    iteration: 0,
    kind: 'pipeline',
    completionPath: '/test-cases',
    timeline: [{
      id: `approval-${workflow.current_stage}`,
      label,
      detail: workflow.status === 'failed' ? (workflow.error ?? `${label} failed.`) : `${label} completed and awaiting approval.`,
      at: new Date(),
      status: workflow.status === 'failed' ? 'failed' : 'complete',
    }],
    error: workflow.error ?? undefined,
    currentStage: workflow.current_stage,
    nextStage: workflow.next_stage,
    logs: workflow.logs,
  }
}

function reconstructJobFromState(projectId: string, projectName: string, state: PipelineState, mode: WorkflowMode = 'quick'): PipelineJob | null {
  if (!state.security_scan && !state.dependency && !state.understanding && !state.generation && !state.verification && !state.quality) {
    return null
  }

  let stage = 'Mapping your project structure'
  let progress = 18
  let status: 'running' | 'paused' | 'complete' | 'failed' = 'running'
  let error: string | undefined
  let iteration = 0
  
  const timeline: Array<{ id: string; label: string; detail: string; at: Date; status: 'complete' | 'failed' | 'active' }> = []
  
  timeline.push({
    id: 't-1',
    label: 'Project received',
    detail: 'Source is secure and ready for AI analysis.',
    at: new Date(),
    status: 'complete'
  })

  if (state.security_scan) {
    const scanDone = state.security_scan.status === 'completed'
    const scanFailed = state.security_scan.status === 'failed'
    timeline.push({
      id: 't-security',
      label: scanFailed ? 'Security scan failed' : scanDone ? 'Security scan complete' : 'Scanning for security risks',
      detail: scanFailed ? (state.security_scan.error_message ?? 'Semgrep failed.') : scanDone ? `${state.security_scan.summary?.total_findings ?? 0} findings detected.` : 'Semgrep is analyzing source files.',
      at: new Date(),
      status: scanFailed ? 'failed' : scanDone ? 'complete' : 'active',
    })
    if (scanFailed) { status = 'failed'; progress = 50; stage = 'Analysis stopped'; error = state.security_scan.error_message ?? 'Security scan failed' }
    else if (scanDone && !state.dependency) { status = 'complete'; progress = 100; stage = 'Security scan complete' }
  }

  if (state.dependency) {
    const isDone = state.dependency.status === 'completed'
    const isFailed = state.dependency.status === 'failed'
    
    timeline.push({
      id: 't-2',
      label: isFailed ? 'Mapping failed' : isDone ? 'Project mapped' : 'Mapping project structure',
      detail: isFailed ? 'Failed to scan files.' : isDone ? `${state.dependency.files.length} source files prepared.` : 'Scanning codebase structure.',
      at: new Date(),
      status: isFailed ? 'failed' : isDone ? 'complete' : 'active'
    })
    
    if (isFailed) {
      status = 'failed'
      progress = 25
      stage = 'Analysis stopped'
      error = 'Repository analysis failed'
    } else if (isDone) {
      progress = 36
      stage = 'Understanding architecture'
    }
  }

  const securityReviewCheckpoint = mode === 'quick'
    && state.security_scan?.status === 'completed'
    && state.dependency?.status === 'completed'
    && !state.understanding
  if (securityReviewCheckpoint) {
    status = 'paused'
    progress = 30
    stage = 'Security analysis complete'
  }

  if (state.understanding) {
    const isDone = state.understanding.status === 'completed'
    const isFailed = state.understanding.status === 'failed'
    
    timeline.push({
      id: 't-3',
      label: isFailed ? 'Analysis paused' : isDone ? 'Code intelligence ready' : 'Understanding architecture',
      detail: isFailed ? 'Failed to analyze code.' : isDone ? (state.understanding.result?.project_summary ?? 'Architecture and behavior analyzed.') : 'Reading files and building assumptions.',
      at: new Date(),
      status: isFailed ? 'failed' : isDone ? 'complete' : 'active'
    })
    
    if (isFailed) {
      status = 'failed'
      progress = 45
      stage = 'Analysis stopped'
      error = state.failure_reason ?? state.understanding.failure_reason ?? 'Test target analysis failed'
    } else if (isDone) {
      progress = 54
      stage = 'Designing test scenarios'
    }
  }

  if (state.generation) {
    const isDone = state.generation.generated_test_cases.length > 0
    
    timeline.push({
      id: 't-4',
      label: isDone ? 'Test suite drafted' : 'Designing test scenarios',
      detail: isDone ? `${state.generation.total_after_deduplication} unique test cases generated.` : 'Creating edge cases and validation plans.',
      at: new Date(),
      status: isDone ? 'complete' : 'active'
    })
    
    if (isDone) {
      progress = 70
      stage = 'Validating tests'
    }
  }

  if (state.verification) {
    const isDone = state.verification.results.length > 0
    
    timeline.push({
      id: 't-5',
      label: isDone ? 'Evidence checked' : 'Validating tests',
      detail: isDone ? `${state.verification.summary.verified} tests verified against source evidence.` : 'Matching actions to expected outcomes.',
      at: new Date(),
      status: isDone ? 'complete' : 'active'
    })
    
    if (isDone) {
      progress = 80
      stage = 'AI verification ready for review'
      status = 'paused'
    }
  }

  if (state.quality) {
    const isDone = state.quality.processing_status === 'completed'
    iteration = state.quality.iterations
    
    timeline.push({
      id: 't-6',
      label: isDone ? 'Quality target met' : 'Improving coverage',
      detail: isDone ? `Final quality score: ${state.quality.final_score}%.` : 'Regenerating weak areas.',
      at: new Date(),
      status: isDone ? 'complete' : 'active'
    })
    
    if (isDone) {
      status = mode === 'review' ? 'paused' : 'complete'
      progress = mode === 'review' ? 92 : 100
      stage = mode === 'review' ? 'Quality results ready for review' : 'Unit test suite ready'
    }
  } else if (state.verification && state.verification.results.length > 0) {
    status = 'paused'
    progress = 80
    stage = 'AI verification ready for review'
  }

  return {
    projectId,
    projectName,
    stage,
    progress,
    status,
    estimatedTime: status === 'complete' ? 'Complete' : 'About 1–3 min',
    iteration,
    timeline,
    error,
    retryAttempt: state.retry_count,
    resumedStage: state.resumed_stage ?? state.failed_stage ?? undefined,
    currentStage: securityReviewCheckpoint ? 'stage_2' : state.quality?.processing_status === 'completed' && mode === 'review' ? 'stage_6' : state.verification && !state.quality ? 'stage_5' : undefined,
    nextStage: securityReviewCheckpoint ? 'stage_3' : undefined,
    logs: state.verification && !state.quality ? [
      'Stage 5 semantic verification completed',
      `Number of tests verified: ${state.verification.results.length}`,
      'Verification duration: Not Available',
      'Waiting for approval before Stage 6',
    ] : undefined,
    kind: state.dependency ? 'pipeline' : 'security_scan',
    completionPath: state.dependency ? '/test-cases' : `/security-report/${projectId}`,
  }
}

const Context = createContext<AppState | null>(null)

export function AppStateProvider({ children }: { children: ReactNode }) {
  const [projects, setProjects] = useState<Project[]>([])
  const [activeProjectId, setActiveProjectIdState] = useState('')
  const [artifactsByProject, setArtifactsByProject] = useState<Record<string, Artifacts>>({})
  const [artifactsLoading, setArtifactsLoading] = useState(false)
  const [activities, setActivities] = useState<Activity[]>([])
  const [uploadMode, setUploadMode] = useState<UploadMode | null>(null)
  const [workflowModes, setWorkflowModes] = useState<Record<string, WorkflowMode>>(() => {
    try { return JSON.parse(localStorage.getItem('testforge-workflow-modes') ?? '{}') as Record<string, WorkflowMode> } catch { return {} }
  })
  const [jobs, setJobs] = useState<Record<string, PipelineJob>>({})
  const jobsRef = useRef(jobs)
  const [developerModes, setDeveloperModes] = useState<Record<string, boolean>>({})
  const developerModesRef = useRef(developerModes)
  useEffect(() => { jobsRef.current = jobs }, [jobs])
  const artifacts = artifactsByProject[activeProjectId] ?? {}
  const setDeveloperMode = (projectId: string, enabled: boolean) => {
    setDeveloperModes((current) => {
      const next = { ...current, [projectId]: enabled }
      developerModesRef.current = next
      return next
    })
  }
  const refreshProjects = async () => {
    const response = await api.projects(0, 100)
    setProjects(response.items)
  }
  const refreshProjectArtifacts = async (projectId: string) => {
    const state = await api.pipelineState(projectId)
    setProjectArtifacts(projectId, {
      securityScan: state.security_scan ?? undefined,
      dependency: state.dependency ?? undefined,
      understanding: state.understanding ?? undefined,
      generation: state.generation ?? undefined,
      verification: state.verification ?? undefined,
      quality: state.quality ?? undefined,
      runtimePreparation: state.runtime_preparation ?? undefined,
    })
  }
  const removeProject = (id: string) => {
    setProjects(projects.filter((project) => project.id !== id))
    setArtifactsByProject((items) => {
      const next = { ...items }
      delete next[id]
      return next
    })
    if (activeProjectId === id) {
      setActiveProjectIdState('')
      sessionStorage.removeItem('activeProjectId')
    }
  }

  const setActiveProjectId = (value: string) => {
    setActiveProjectIdState(value)
    if (value) sessionStorage.setItem('activeProjectId', value)
    else sessionStorage.removeItem('activeProjectId')
  }
  const setArtifacts: AppState['setArtifacts'] = (value) => setArtifactsByProject((all) => {
    const current = all[activeProjectId] ?? {}
    return { ...all, [activeProjectId]: typeof value === 'function' ? value(current) : value }
  })
  const setProjectArtifacts = (projectId: string, value: Artifacts) => {
    setArtifactsByProject((all) => ({ ...all, [projectId]: value }))
  }
  const record = (label: string, detail: string) => setActivities((items) => [
    { id: crypto.randomUUID(), label, detail, at: new Date() },
    ...items,
  ].slice(0, 12))
  const updateJob = (projectId: string, update: Partial<PipelineJob>) => {
    setJobs((current) => ({
      ...current,
      [projectId]: { ...current[projectId], ...update },
    }))
  }
  const addJobActivity = (
    projectId: string,
    label: string,
    detail: string,
    status: JobActivity['status'] = 'complete',
  ) => {
    setJobs((current) => ({
      ...current,
      [projectId]: {
        ...current[projectId],
        timeline: [
          ...(current[projectId]?.timeline ?? []),
          { id: crypto.randomUUID(), label, detail, at: new Date(), status },
        ],
      },
    }))
  }

  const executeSecurityScan = (
    project: Project,
    operation: () => Promise<SecurityScan>,
    retryAttempt = 0,
  ) => {
    const projectId = project.id
    setActiveProjectId(projectId)
    setJobs((current) => ({
      ...current,
      [projectId]: {
        projectId,
        projectName: project.name,
        stage: 'Scanning source code with Semgrep',
        progress: 12,
        status: 'running',
        estimatedTime: 'About 1–2 min',
        iteration: 0,
        retryAttempt,
        kind: 'security_scan',
        completionPath: `/security-report/${projectId}`,
        timeline: [{
          id: crypto.randomUUID(),
          label: 'Project received',
          detail: 'Source is ready for security analysis.',
          at: new Date(),
          status: 'complete',
        }],
      },
    }))
    record('Security scan started', project.name)

    void (async () => {
      try {
        updateJob(projectId, { progress: 50 })
        let securityScan = await operation()
        for (let attempt = 0; securityScan.status === 'running' && attempt < 360; attempt += 1) {
          await new Promise((resolve) => window.setTimeout(resolve, 1000))
          securityScan = await api.latestSecurityScan(projectId)
        }
        setProjectArtifacts(projectId, { securityScan })
        if (securityScan.status !== 'completed') {
          throw new Error(securityScan.error_message ?? 'Security scan did not complete')
        }
        addJobActivity(projectId, 'Security scan complete', `${securityScan.summary?.total_findings ?? 0} findings detected by Semgrep.`)
        updateJob(projectId, { stage: 'Security scan complete', progress: 100, status: 'complete', estimatedTime: 'Complete' })
        record('Security scan completed', `${project.name}: ${securityScan.summary?.total_findings ?? 0} findings`)
      } catch (reason) {
        const message = securityScanErrorMessage(reason)
        const failedScan = await api.latestSecurityScan(projectId).catch(() => undefined)
        if (failedScan) setProjectArtifacts(projectId, { securityScan: failedScan })
        addJobActivity(projectId, 'Security scan failed', message, 'failed')
        updateJob(projectId, { stage: 'Security scan stopped', status: 'failed', error: message })
        record('Security scan failed', `${project.name}: ${message}`)
      }
    })()
  }

  const startSecurityScan = (project: Project) => {
    if (jobs[project.id]?.status === 'running') return
    executeSecurityScan(project, () => api.securityScan(project.id))
  }

  const retrySecurityScan = (project: Project) => {
    if (jobs[project.id]?.status === 'running') return
    const scan = artifactsByProject[project.id]?.securityScan
    if (!scan || scan.status !== 'failed') return
    executeSecurityScan(
      project,
      () => api.retrySecurityScan(scan.run_id),
      scan.retry_count + 1,
    )
  }

  const applyApprovalResponse = (response: WorkflowResponse, preserveTimeline = false) => {
    const projectId = response.project.id
    setProjectArtifacts(projectId, {
      securityScan: response.security_scan ?? undefined,
      dependency: response.dependency ?? undefined,
      understanding: response.pipeline ?? undefined,
      generation: response.generation ?? undefined,
    })
    setJobs((current) => {
      const next = approvalJob(response)
      if (preserveTimeline && current[projectId]) {
        next.timeline = [
          ...current[projectId].timeline.filter((item) => item.status !== 'active'),
          ...next.timeline,
        ]
      }
      return { ...current, [projectId]: next }
    })
  }

  const beginApprovalWorkflow = (workflow: WorkflowResponse, mode: WorkflowMode = 'quick') => {
    const modes = { ...workflowModes, [workflow.project.id]: mode }
    setWorkflowModes(modes)
    localStorage.setItem('testforge-workflow-modes', JSON.stringify(modes))
    setActiveProjectId(workflow.project.id)
    applyApprovalResponse(workflow)
    record(`${workflow.completed_stage?.replace('_', ' ')} completed`, workflow.project.name)
  }

  const startQuickWorkflow = (project: Project) => {
    const projectId = project.id
    void (async () => {
      const label = 'Repository and security analysis'
      updateJob(projectId, { currentStage: 'stage_2', nextStage: null, stage: label, progress: 24, status: 'running', estimatedTime: 'In progress', error: undefined, logs: [`Starting ${label}`] })
      addJobActivity(projectId, `${label} started`, 'Discovering dependencies and scanning the repository.', 'active')
      const poll = window.setInterval(() => {
        void api.workflowState(projectId).then((live) => {
          setProjectArtifacts(projectId, { securityScan: live.security_scan ?? undefined, dependency: live.dependency ?? undefined, understanding: live.pipeline ?? undefined, generation: live.generation ?? undefined })
          if (live.logs.length) updateJob(projectId, { logs: live.logs })
          if (live.status === 'failed') applyApprovalResponse(live, true)
        }).catch(() => undefined)
      }, 1000)
      try {
        const response = await api.continueWorkflow(projectId, 'stage_1')
        applyApprovalResponse(response, true)
        if (response.status === 'failed') return
        updateJob(projectId, { stage: 'Security analysis complete', progress: 30, status: 'paused', currentStage: 'stage_2', nextStage: 'stage_3', estimatedTime: 'Paused' })
        addJobActivity(projectId, 'Security analysis complete', 'Review the persisted security findings before generation continues.')
        record('Security analysis completed', project.name)
      } catch (reason) {
        const message = reason instanceof Error ? reason.message : `${label} failed`
        const persisted = await api.workflowState(projectId).catch(() => undefined)
        if (persisted) applyApprovalResponse(persisted, true)
        updateJob(projectId, { status: 'failed', stage: 'Security analysis failed', error: message })
        addJobActivity(projectId, `${label} failed`, message, 'failed')
        record('Stage failed', `${project.name}: ${message}`)
      } finally {
        window.clearInterval(poll)
      }
    })()
  }

  const approveNextStage = (project: Project) => {
    const job = jobs[project.id]
    if (!job?.currentStage || job.status === 'running') return
    if (job.currentStage === 'stage_4' && job.status !== 'failed') return
    const fromStage: 'stage_1' | 'stage_2' | 'stage_3' = job.status === 'failed'
      ? (`stage_${Math.max(1, Number(job.currentStage.slice(-1)) - 1)}` as 'stage_1' | 'stage_2' | 'stage_3')
      : job.currentStage as 'stage_1' | 'stage_2' | 'stage_3'
    if (job.status !== 'failed' && !job.nextStage) return
    updateJob(project.id, {
      status: 'running',
      stage: job.status === 'failed' ? `Retrying ${job.currentStage.replace('_', ' ')}` : `Running ${job.nextStage?.replace('_', ' ')}`,
      estimatedTime: 'In progress',
    })
    void (async () => {
      try {
        let response = await api.continueWorkflow(project.id, fromStage)
        while (
          (workflowModes[project.id] ?? 'quick') === 'quick'
          &&
          response.status === 'waiting_for_approval'
          && response.current_stage !== 'stage_2'
          && response.current_stage !== 'stage_4'
        ) {
          response = await api.continueWorkflow(
            project.id,
            response.current_stage as 'stage_1' | 'stage_2' | 'stage_3',
          )
        }
        applyApprovalResponse(response)
        record(`${response.completed_stage?.replace('_', ' ')} completed`, project.name)
      } catch (reason) {
        const message = reason instanceof Error ? reason.message : 'Stage execution failed'
        const persisted = await api.workflowState(project.id).catch(() => undefined)
        if (persisted) applyApprovalResponse(persisted)
        else updateJob(project.id, { status: 'failed', error: message, stage: 'Stage failed' })
        record('Stage failed', `${project.name}: ${message}`)
      }
    })()
  }

  const startPipeline = (project: Project) => {
    const projectId = project.id
    const securityScan = artifactsByProject[projectId]?.securityScan
    if (!securityScan || securityScan.status !== 'completed') return
    setActiveProjectId(projectId)
    setJobs((current) => ({
      ...current,
      [projectId]: {
        projectId,
        projectName: project.name,
        stage: 'Mapping your project structure',
        progress: 18,
        status: 'running',
        estimatedTime: 'About 3–5 min',
        iteration: 0,
        kind: 'pipeline',
        completionPath: '/test-cases',
        timeline: [{
          id: crypto.randomUUID(),
          label: 'Security scan complete',
          detail: `${securityScan.summary?.total_findings ?? 0} findings detected by Semgrep.`,
          at: new Date(),
          status: 'complete',
        }],
      },
    }))
    record('Test generation started', project.name)

    void (async () => {
      try {
        const dependencyStart = await api.dependency(projectId)
        const dependency = await api.dependencyRun(dependencyStart.run_id)
        setProjectArtifacts(projectId, { securityScan, dependency })
        addJobActivity(projectId, 'Project mapped', `${dependency.files.length} source files prepared for analysis.`)

        updateJob(projectId, { stage: 'Understanding architecture and behavior', progress: 36, estimatedTime: 'About 2–4 min' })
        const understanding = await api.understand(projectId, dependency.run_id)
        setProjectArtifacts(projectId, { securityScan, dependency, understanding })
        addJobActivity(projectId, 'Code intelligence ready', understanding.result?.project_summary ?? 'Architecture and behavior were analyzed.')

        if (developerModesRef.current[projectId]) {
          updateJob(projectId, {
            stage: 'Repository analysis ready',
            progress: 54,
            status: 'paused',
            pausedAfterStage3: true,
            estimatedTime: 'Waiting for review',
          })
          addJobActivity(projectId, 'Pipeline paused after Stage 3', 'Developer Mode is enabled. Review the Stage 3 response, then continue to Stage 4.', 'active')
          return
        }

        updateJob(projectId, { stage: 'Designing high-value test scenarios', progress: 54, estimatedTime: 'About 2 min' })
        const generation = await api.generate(projectId, understanding.run_id)
        setProjectArtifacts(projectId, { securityScan, dependency, understanding, generation })
        addJobActivity(projectId, 'Test suite drafted', `${generation.total_after_deduplication} unique test cases generated.`)

        updateJob(projectId, { stage: 'Validating tests against your code', progress: 70, estimatedTime: 'About 1–2 min' })
        const verification = await api.verify(projectId, understanding.run_id, generation.generated_test_cases)
        setProjectArtifacts(projectId, { securityScan, dependency, understanding, generation, verification })
        addJobActivity(projectId, 'Evidence checked', `${verification.summary.verified} tests verified against source evidence.`)

        updateJob(projectId, { stage: 'Improving weak coverage automatically', progress: 84, estimatedTime: 'Under a minute', iteration: 1 })
        let quality = await api.optimize(projectId, understanding.run_id, generation.generated_test_cases, verification)
        for (let resumeAttempt = 1; quality.processing_status === 'partial_success' && resumeAttempt <= 2; resumeAttempt += 1) {
          setProjectArtifacts(projectId, { securityScan, dependency, understanding, generation: quality.test_generation, verification: quality.test_verification, quality })
          updateJob(projectId, { stage: 'Waiting for AI capacity', status: 'running', estimatedTime: 'Resuming automatically', iteration: quality.iterations })
          addJobActivity(projectId, 'Optimization paused', `Providers are cooling down. Resume attempt ${resumeAttempt} will start automatically.`)
          await new Promise(resolve => window.setTimeout(resolve, 5000))
          quality = await api.optimize(projectId, understanding.run_id, quality.test_generation.generated_test_cases, quality.test_verification)
        }
        addJobActivity(projectId, 'Quality target evaluated', `${quality.iterations} optimization iteration${quality.iterations === 1 ? '' : 's'} completed.`)

        updateJob(projectId, { stage: 'Preparing your final workspace', progress: 96, estimatedTime: 'A few seconds', iteration: quality.iterations })
        const finalArtifacts: Artifacts = {
          securityScan,
          dependency,
          understanding,
          generation: quality.test_generation,
          verification: quality.test_verification,
          quality,
        }
        setProjectArtifacts(projectId, finalArtifacts)
        addJobActivity(projectId, 'Workspace ready', `Final quality score: ${quality.final_score}%.`)
        updateJob(projectId, { stage: 'Analysis complete', progress: 100, status: 'complete', estimatedTime: 'Complete' })
        record('Analysis completed', `${project.name} reached a quality score of ${quality.final_score}%`)
      } catch (reason) {
        const message = reason instanceof Error ? reason.message : 'Analysis could not be completed'
        addJobActivity(projectId, 'Analysis paused', message, 'failed')
        updateJob(projectId, { stage: 'Analysis stopped', status: 'failed', error: message })
        record('Analysis failed', `${project.name}: ${message}`)
      }
    })()
  }

  const continuePipeline = (project: Project, artifactOverride?: Artifacts) => {
    const projectId = project.id
    const current = artifactOverride ?? artifactsByProject[projectId]
    const securityScan = current?.securityScan
    const dependency = current?.dependency
    const understanding = current?.understanding
    const generation = current?.generation
    const existingVerification = current?.verification
    const existingQuality = current?.quality
    if (!securityScan || !dependency || !understanding?.result || !generation) return

    updateJob(projectId, {
      stage: existingVerification ? 'Improving weak coverage automatically' : 'Validating tests against your code',
      progress: existingVerification ? 84 : 70,
      status: 'running',
      currentStage: existingVerification ? 'stage_6' : 'stage_5',
      pausedAfterStage3: false,
      estimatedTime: 'About 1–2 min',
      logs: [existingVerification ? 'Starting Stage 6 quality optimization' : 'Starting Stage 5 semantic verification'],
    })
    addJobActivity(projectId, existingVerification ? 'Stage 5 approved' : 'Stage 4 approved', existingVerification ? 'Starting Stage 6 quality optimization.' : 'Starting Stage 5 semantic verification.', 'active')

    const downstreamPoll = window.setInterval(() => {
      void api.pipelineState(projectId).then((live) => {
        setProjectArtifacts(projectId, {
          securityScan: live.security_scan ?? undefined,
          dependency: live.dependency ?? undefined,
          understanding: live.understanding ?? undefined,
          generation: live.generation ?? undefined,
          verification: live.verification ?? undefined,
          quality: live.quality ?? undefined,
          runtimePreparation: live.runtime_preparation ?? undefined,
        })
      }).catch(() => undefined)
    }, 1000)

    void (async () => {
      try {
        if (existingQuality) {
          updateJob(projectId, { stage: 'Running Runtime Validation', currentStage: 'stage_7', progress: 96, logs: ['Starting Stage 7 runtime validation'] })
          const runtime = await api.startRuntimeValidation(projectId, understanding.run_id, 'http://127.0.0.1:8001')
          sessionStorage.setItem(`testforge-runtime-run:${projectId}`, runtime.run_id)
          addJobActivity(projectId, 'Runtime validation complete', `Runtime run ${runtime.run_id} completed with status ${runtime.status}.`)
          updateJob(projectId, { stage: 'Runtime validation ready for review', progress: 100, status: 'complete', currentStage: 'stage_7', estimatedTime: 'Complete', completionPath: `/runtime-validation/${projectId}` })
          record('Runtime validation completed', project.name)
          return
        }
        let verification = existingVerification
        if (!verification) {
          const started = performance.now()
          verification = await api.verify(projectId, understanding.run_id, generation.generated_test_cases)
          const durationMs = Math.round(performance.now() - started)
          setProjectArtifacts(projectId, { securityScan, dependency, understanding, generation, verification })
          addJobActivity(projectId, 'Evidence checked', `${verification.summary.verified} tests verified against source evidence.`)
          if ((workflowModes[projectId] ?? 'quick') === 'review') {
            updateJob(projectId, {
              stage: 'AI verification ready for review',
              progress: 80,
              status: 'paused',
              currentStage: 'stage_5',
              estimatedTime: 'Waiting for approval',
              logs: [
                'Stage 5 semantic verification completed',
                `Verification duration: ${durationMs} ms`,
                `Number of tests verified: ${verification.results.length}`,
                'Waiting for approval before Stage 6',
              ],
            })
            return
          }
        }

        updateJob(projectId, { stage: 'Improving weak coverage automatically', currentStage: 'stage_6', progress: 84, estimatedTime: 'Under a minute', iteration: 1, logs: ['Starting Stage 6 quality optimization'] })
        let quality = await api.optimize(projectId, understanding.run_id, generation.generated_test_cases, verification)
        for (let resumeAttempt = 1; quality.processing_status === 'partial_success' && resumeAttempt <= 2; resumeAttempt += 1) {
          setProjectArtifacts(projectId, { securityScan, dependency, understanding, generation: quality.test_generation, verification: quality.test_verification, quality })
          updateJob(projectId, { stage: 'Waiting for AI capacity', status: 'running', estimatedTime: 'Resuming automatically', iteration: quality.iterations })
          addJobActivity(projectId, 'Optimization paused', `Providers are cooling down. Resume attempt ${resumeAttempt} will start automatically.`)
          await new Promise(resolve => window.setTimeout(resolve, 5000))
          quality = await api.optimize(projectId, understanding.run_id, quality.test_generation.generated_test_cases, quality.test_verification)
        }
        addJobActivity(projectId, 'Quality target evaluated', `${quality.iterations} optimization iteration${quality.iterations === 1 ? '' : 's'} completed.`)

        updateJob(projectId, { stage: 'Preparing your final workspace', progress: 96, estimatedTime: 'A few seconds', iteration: quality.iterations })
        setProjectArtifacts(projectId, {
          securityScan,
          dependency,
          understanding,
          generation: quality.test_generation,
          verification: quality.test_verification,
          quality,
        })
        addJobActivity(projectId, 'Workspace ready', `Final quality score: ${quality.final_score}%.`)
        if ((workflowModes[projectId] ?? 'quick') === 'quick') {
          updateJob(projectId, { stage: 'Running Runtime Validation', currentStage: 'stage_7', progress: 96, estimatedTime: 'About 1–2 min', logs: ['Starting Stage 7 runtime validation'] })
          const runtime = await api.startRuntimeValidation(projectId, understanding.run_id, 'http://127.0.0.1:8001')
          sessionStorage.setItem(`testforge-runtime-run:${projectId}`, runtime.run_id)
          addJobActivity(projectId, 'Runtime validation complete', `Runtime run ${runtime.run_id} completed with status ${runtime.status}.`)
          updateJob(projectId, { stage: 'Runtime Validation ready for review', progress: 100, status: 'complete', estimatedTime: 'Complete', completionPath: `/runtime-validation/${projectId}` })
          record('Runtime validation completed', project.name)
        } else {
          updateJob(projectId, {
            stage: 'Quality results ready for review',
            progress: 92,
            status: 'paused',
            currentStage: 'stage_6',
            estimatedTime: 'Waiting for approval',
            logs: ['Stage 6 quality optimization completed', `Final quality score: ${quality.final_score}%`, 'Waiting for approval before Stage 7'],
          })
          record('Stage 6 completed', `${project.name} reached a quality score of ${quality.final_score}%`)
        }
      } catch (reason) {
        const message = reason instanceof Error ? reason.message : 'Analysis could not be completed'
        addJobActivity(projectId, 'Analysis paused', message, 'failed')
        updateJob(projectId, { stage: 'Analysis stopped', status: 'failed', error: message })
        record('Analysis failed', `${project.name}: ${message}`)
      } finally {
        window.clearInterval(downstreamPoll)
      }
    })()
  }

  const continueAfterSecurity = (project: Project) => {
    const projectId = project.id
    const job = jobs[projectId]
    if ((workflowModes[projectId] ?? 'quick') !== 'quick' || job?.status === 'running') return
    const transitions = [
      { from: 'stage_2' as const, stage: 'stage_3' as const, label: 'Test target analysis', progress: 45 },
      { from: 'stage_3' as const, stage: 'stage_4' as const, label: 'Unit test generation', progress: 60 },
    ]
    void (async () => {
      let latest: WorkflowResponse | undefined
      for (const transition of transitions) {
        updateJob(projectId, { currentStage: transition.stage, nextStage: null, stage: transition.label, progress: transition.progress, status: 'running', estimatedTime: 'In progress', error: undefined, logs: [`Starting ${transition.label}`] })
        addJobActivity(projectId, `${transition.label} started`, `${transition.label} is running.`, 'active')
        const poll = window.setInterval(() => {
          void api.workflowState(projectId).then((live) => {
            setProjectArtifacts(projectId, { securityScan: live.security_scan ?? undefined, dependency: live.dependency ?? undefined, understanding: live.pipeline ?? undefined, generation: live.generation ?? undefined })
            if (live.logs.length) updateJob(projectId, { logs: live.logs })
            if (live.status === 'failed') applyApprovalResponse(live, true)
          }).catch(() => undefined)
        }, 1000)
        try {
          latest = await api.continueWorkflow(projectId, transition.from)
          applyApprovalResponse(latest, true)
          if (latest.status === 'failed') return
          addJobActivity(projectId, `${transition.label} completed`, `${transition.label} artifacts are ready.`)
          record(`${transition.label} completed`, project.name)
        } catch (reason) {
          const message = reason instanceof Error ? reason.message : `${transition.label} failed`
          const persisted = await api.workflowState(projectId).catch(() => undefined)
          if (persisted) applyApprovalResponse(persisted, true)
          updateJob(projectId, { status: 'failed', stage: `${transition.label} failed`, error: message })
          addJobActivity(projectId, `${transition.label} failed`, message, 'failed')
          record('Stage failed', `${project.name}: ${message}`)
          return
        } finally {
          window.clearInterval(poll)
        }
      }
      if (!latest?.security_scan || !latest.dependency || !latest.pipeline || !latest.generation) return
      const downstreamArtifacts: Artifacts = {
        securityScan: latest.security_scan,
        dependency: latest.dependency,
        understanding: latest.pipeline,
        generation: latest.generation,
      }
      setProjectArtifacts(projectId, downstreamArtifacts)
      continuePipeline(project, downstreamArtifacts)
    })()
  }

  const resumePipeline = (project: Project) => {
    const projectId = project.id
    setActiveProjectId(projectId)

    const currentArtifacts = artifactsByProject[projectId] ?? {}
    const completedStages = new Set<number>()
    let currentStageNum = 2
    let progress = 18

    completedStages.add(1)

    if (currentArtifacts.dependency?.status === 'completed') {
      completedStages.add(2)
      currentStageNum = 3
      progress = 36
    }
    if (currentArtifacts.understanding?.status === 'completed') {
      completedStages.add(3)
      currentStageNum = 4
      progress = 54
    }
    if (currentArtifacts.generation) {
      completedStages.add(4)
      currentStageNum = 5
      progress = 70
    }
    if (currentArtifacts.verification) {
      completedStages.add(5)
      currentStageNum = 6
      progress = 84
    }

    const resumeLabel = `Resuming from Stage ${currentStageNum}...`

    setJobs((current) => {
      const job = current[projectId]
      return {
        ...current,
        [projectId]: {
          projectId,
          projectName: project.name,
          stage: resumeLabel,
          progress: progress,
          status: 'running',
          estimatedTime: job?.estimatedTime ?? 'About 2–4 min',
          iteration: job?.iteration ?? 0,
          kind: 'pipeline',
          completionPath: '/test-cases',
          timeline: [
            ...(job?.timeline ?? []),
            {
              id: crypto.randomUUID(),
              label: 'Pipeline resumed',
              detail: `Continuing analysis from Stage ${currentStageNum}.`,
              at: new Date(),
              status: 'active',
            }
          ],
        }
      }
    })

    record('Analysis resumed', project.name)

    void (async () => {
      try {
        const runId = currentArtifacts.understanding?.run_id
        if (runId) await api.retryPipeline(runId)
        else await api.resume(projectId)
        const state = await api.pipelineState(projectId)
        
        const finalArtifacts: Artifacts = {
          securityScan: state.security_scan ?? undefined,
          dependency: state.dependency ?? undefined,
          understanding: state.understanding ?? undefined,
          generation: state.generation ?? undefined,
          verification: state.verification ?? undefined,
          quality: state.quality ?? undefined,
        }
        setProjectArtifacts(projectId, finalArtifacts)

        if (!completedStages.has(2) && state.dependency) {
          addJobActivity(projectId, 'Project mapped', `${state.dependency.files.length} source files prepared for analysis.`)
        }
        if (!completedStages.has(3) && state.understanding) {
          addJobActivity(projectId, 'Code intelligence ready', state.understanding.result?.project_summary ?? 'Architecture and behavior were analyzed.')
        }
        if (!completedStages.has(4) && state.generation) {
          addJobActivity(projectId, 'Test suite drafted', `${state.generation.total_after_deduplication} unique test cases generated.`)
        }
        if (!completedStages.has(5) && state.verification) {
          addJobActivity(projectId, 'Evidence checked', `${state.verification.summary.verified} tests verified against source evidence.`)
        }
        if (state.quality) {
          addJobActivity(projectId, 'Quality target evaluated', `${state.quality.iterations} optimization iteration(s) completed.`)
          addJobActivity(projectId, 'Workspace ready', `Final quality score: ${state.quality.final_score}%.`)
          updateJob(projectId, {
            stage: 'Analysis complete',
            progress: 100,
            status: 'complete',
            estimatedTime: 'Complete',
          iteration: state.quality.iterations
            , retryAttempt: state.retry_count,
            resumedStage: state.resumed_stage ?? undefined
          })
          record('Analysis completed', `${project.name} reached a quality score of ${state.quality.final_score}%`)
        } else {
          updateJob(projectId, {
            stage: 'Analysis complete',
            progress: 100,
            status: 'complete',
            estimatedTime: 'Complete'
          })
        }
      } catch (reason) {
        const message = reason instanceof Error ? reason.message : 'Analysis could not be resumed'
        addJobActivity(projectId, 'Analysis paused', message, 'failed')
        updateJob(projectId, { stage: 'Analysis stopped', status: 'failed', error: message })
        record('Analysis failed', `${project.name}: ${message}`)
      }
    })()
  }

  useEffect(() => {
    if (!activeProjectId) return
    const projectId = activeProjectId
    let cancelled = false
    setArtifactsLoading(true)
    let timer: number | undefined
    const poll = () => Promise.all([
      api.pipelineState(projectId),
      api.workflowState(projectId),
    ]).then(([state, workflow]) => {
      if (cancelled) return
      setProjectArtifacts(projectId, {
        securityScan: state.security_scan ?? undefined,
        dependency: state.dependency ?? undefined,
        understanding: state.understanding ?? undefined,
        generation: state.generation ?? undefined,
        verification: state.verification ?? undefined,
        quality: state.quality ?? undefined,
      })

      // Reconstruct job state from backend data if it is missing or completed/failed
      const project = projects.find((p) => p.id === projectId)
      if (project) {
        const liveJob = jobsRef.current[projectId]
        const quickDownstreamRunning = (
          (workflowModes[projectId] ?? 'quick') === 'quick'
          && liveJob?.status === 'running'
          && Number(liveJob.currentStage?.slice(-1) ?? 0) >= 5
        )
        if (
          !quickDownstreamRunning
          &&
          ((workflow.current_stage === 'stage_4' && !state.verification) || !state.generation)
          && (
            workflow.status === 'failed'
            || workflow.status === 'waiting_for_approval'
            || workflow.status === 'running'
          )
        ) {
          setProjectArtifacts(projectId, {
            securityScan: workflow.security_scan ?? undefined,
            dependency: workflow.dependency ?? undefined,
            understanding: workflow.pipeline ?? undefined,
            generation: workflow.generation ?? state.generation ?? undefined,
          })
          setJobs((current) => ({
            ...current,
            [projectId]: approvalJob(workflow),
          }))
          return
        }
        const reconstructed = reconstructJobFromState(projectId, project.name, state, workflowModes[projectId] ?? 'quick')
        if (reconstructed) {
          setJobs((current) => {
            if (
              current[projectId]
              && ['running', 'paused'].includes(current[projectId].status)
            ) {
              return current
            }
            return {
              ...current,
              [projectId]: reconstructed
            }
          })
        }
      }

      if (
        state.understanding?.status === 'running'
        || state.quality?.processing_status === 'in_progress'
        || state.quality?.processing_status === 'partial_success'
      ) {
        timer = window.setTimeout(poll, 3000)
      }
    }).catch(() => {
      if (!cancelled) timer = window.setTimeout(poll, 5000)
    }).finally(() => { if (!cancelled) setArtifactsLoading(false) })
    void poll()
    return () => { cancelled = true; if (timer !== undefined) window.clearTimeout(timer) }
  }, [activeProjectId, projects, workflowModes])

  const value = useMemo(() => ({
    projects, setProjects, refreshProjects, removeProject, activeProjectId, setActiveProjectId, artifacts, setArtifacts, artifactsLoading, refreshProjectArtifacts,
    activities, record, uploadMode, openUpload: setUploadMode,
    closeUpload: () => setUploadMode(null), jobs, startSecurityScan, retrySecurityScan, startPipeline, resumePipeline,
    developerMode: (projectId: string) => Boolean(developerModes[projectId]),
    setDeveloperMode, continuePipeline, beginApprovalWorkflow, startQuickWorkflow, continueAfterSecurity, approveNextStage,
    workflowMode: (projectId: string) => workflowModes[projectId] ?? 'quick',
  }), [projects, activeProjectId, artifacts, artifactsLoading, activities, uploadMode, jobs, resumePipeline, developerModes, workflowModes])
  return <Context.Provider value={value}>{children}</Context.Provider>
}

export function useAppState() {
  const state = useContext(Context)
  if (!state) throw new Error('AppStateProvider is missing')
  return state
}
