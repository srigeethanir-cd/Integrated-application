import { useMemo, useRef, useState, useEffect } from 'react'
import { CheckCircle2, Circle, CircleAlert, Download, Play, SearchCode, Sparkles, X } from 'lucide-react'
import type { DependencyRun, Project, RuntimeValidationReport, SecurityScan, TestGeneration, VerificationResult, UnderstandingResponse } from '../api/types'
import type { PipelineJob } from '../state/app-state'
import { Badge, Button } from './ui'
import { TestExplorer } from './TestExplorer'

interface GenerateWorkspaceProps {
  job: PipelineJob
  project?: Project
  dependency?: DependencyRun
  understanding?: UnderstandingResponse
  security?: SecurityScan
  generation?: TestGeneration
  verification?: VerificationResult
  runtime: RuntimeValidationReport | null
  coverage: number | null
  elapsed: string
  onResume: () => void
  onRuntime: () => void
  onExport: () => void
}

const taskNames = [
  'Project Initialization',
  'Repository Analysis',
  'Test Target Discovery',
  'Generating Unit Tests',
  'AI Test Review',
  'Test Quality Review',
  'Runtime Validation',
]

const pipelineNames = ['Repository', 'Security', 'Target Discovery', 'Generation', 'Verification', 'Optimization', 'Runtime']

function cleanActivity(value: string) {
  return value
    .replace(/\bstage\s*[1-7]\b/gi, '')
    .replace(/semantic verification/gi, 'AI test review')
    .replace(/quality optimization/gi, 'test quality review')
    .replace(/waiting for approval|awaiting approval|ready for review/gi, 'ready to continue')
    .replace(/\s{2,}/g, ' ')
    .replace(/^\s*[·:–—-]\s*/, '')
    .trim()
}

function language(dependency?: DependencyRun) {
  const analysis = dependency?.analysis ?? {}
  const explicit = analysis.language ?? analysis.primary_language
  if (typeof explicit === 'string' && explicit.trim()) return explicit
  const detected = [...new Set((dependency?.files ?? []).map((file) => file.language).filter(Boolean))]
  return detected.length ? detected.join(', ') : null
}

export function GenerateWorkspace({ job, project, dependency, understanding, security, generation, verification, runtime, coverage, elapsed, onResume, onRuntime, onExport }: GenerateWorkspaceProps) {
  const [fullLogs, setFullLogs] = useState(false)
  const feedRef = useRef<HTMLDivElement>(null)
  const logsRef = useRef<HTMLOListElement>(null)
  const stageNumber = Number(job.currentStage?.slice(-1) ?? 1)
  const currentTask = taskNames[stageNumber - 1]
  const stage3 = understanding?.result
  const tests = generation?.generated_test_cases ?? []
  const findings = security?.findings ?? []
  const status = job.status === 'paused' ? 'Paused' : job.status === 'complete' ? 'Completed' : job.status === 'failed' ? 'Failed' : 'Running'
  const agent = ['Project Agent', 'Repository Agent', 'Analysis Agent', 'Test Generation Agent', 'Verification Agent', 'Quality Agent', 'Runtime Agent'][stageNumber - 1]
  const activities = useMemo(() => job.timeline.map((event) => ({ ...event, label: cleanActivity(event.label), detail: cleanActivity(event.detail) })).filter((event) => event.label || event.detail), [job.timeline])
  const summary = [
    project?.name ? ['Repository', project.name] : null,
    language(dependency) && ['Language', language(dependency)!],
    dependency ? ['Files analyzed', String(dependency.files.length)] : null,
    stage3?.functions ? ['Functions discovered', String(stage3.functions.length)] : null,
    stage3?.classes ? ['Classes discovered', String(stage3.classes.length)] : null,
    security?.summary ? ['Security findings', String(security.summary.total_findings)] : null,
    generation ? ['Generated tests', String(generation.total_after_deduplication)] : null,
    coverage != null ? ['Coverage estimate', `${coverage}%`] : null,
  ].filter((item): item is [string, string] => Boolean(item))
  const visibleLogs = fullLogs ? job.logs ?? [] : (job.logs ?? []).slice(-6)

  useEffect(() => {
    if (job.status === 'running') feedRef.current?.scrollTo({ top: feedRef.current.scrollHeight, behavior: 'smooth' })
  }, [activities.length, job.status])
  useEffect(() => {
    if (job.status === 'running') logsRef.current?.scrollTo({ top: logsRef.current.scrollHeight, behavior: 'smooth' })
  }, [job.logs?.length, job.status])

  return <section className="execution-console">
    <header className="console-header"><div className="console-title"><small>AI Execution Console</small><h1>{job.projectName}</h1></div><div className="console-meta"><span>{currentTask}</span><span><Sparkles size={13} /> {agent}</span><span className={`generate-status ${job.status}`}><Badge tone={job.status === 'failed' ? 'danger' : job.status === 'complete' ? 'success' : job.status === 'paused' ? 'warning' : 'info'}>{status}</Badge></span><span>{elapsed}</span><strong>{job.progress}%</strong></div><div className="console-progress"><i style={{ width: `${job.progress}%` }} /></div></header>

    <nav className="console-pipeline" aria-label="Generation workflow progress">{pipelineNames.map((name, index) => { const number = index + 1; const complete = number < stageNumber || job.status === 'complete'; const current = number === stageNumber && job.status !== 'complete'; const failed = current && job.status === 'failed'; return <div key={name} className={complete ? 'complete' : failed ? 'failed' : current ? 'current' : 'pending'}><span>{complete ? <CheckCircle2 size={15} /> : failed ? <X size={13} /> : current ? <SearchCode size={14} /> : <Circle size={13} />}</span><strong>{name}</strong></div> })}</nav>

    {summary.length > 0 && <dl className="console-metrics" aria-label="Workspace metrics">{summary.map(([label, value]) => <div key={label}><dd>{value}</dd><dt>{label}</dt></div>)}</dl>}

    <main className="console-content">
      <section className="console-section console-activity"><header><h2>Activity</h2><small>{activities.length} events</small></header><div ref={feedRef}>{activities.length ? activities.map((event, index) => <article key={event.id} className={`${event.status} ${index === activities.length - 1 ? 'latest' : ''}`}><span>{event.status === 'failed' ? <CircleAlert size={15} /> : event.status === 'active' ? <SearchCode size={15} /> : <CheckCircle2 size={15} />}</span><strong>{event.label || event.detail}</strong><time>{event.at.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</time>{event.label && event.detail && event.label !== event.detail && <p>{event.detail}</p>}<small>{event.status === 'active' ? 'Running' : event.status === 'failed' ? 'Failed' : 'Completed'}</small></article>) : <div className="console-empty">No activity has been recorded.</div>}</div></section>

      <section className="console-section console-logs"><header><h2>Execution Logs</h2><small>{job.logs?.length ?? 0} entries</small></header>{visibleLogs.length ? <ol ref={logsRef}>{visibleLogs.map((entry, index) => <li key={`${index}-${entry}`}><code>{entry}</code></li>)}</ol> : <div className="console-log-empty">No execution logs were returned.</div>}{(job.logs?.length ?? 0) > 6 && <button onClick={() => setFullLogs((current) => !current)}>{fullLogs ? 'Show Latest Logs' : 'View Full Logs'}</button>}</section>

      {(understanding || findings.length > 0) && <details className="console-evidence"><summary>Repository evidence</summary>{understanding && <pre>{JSON.stringify(understanding, null, 2)}</pre>}{findings.length > 0 && <div className="console-findings">{findings.map((finding) => <article key={finding.id}><Badge tone={/critical|high|error/i.test(finding.severity) ? 'danger' : 'warning'}>{finding.severity}</Badge><strong>{finding.rule_id}</strong><small>{finding.file}:{finding.line}</small><p>{finding.message}</p></article>)}</div>}</details>}

      {generation && <section className="console-tests"><header><h2>Generated Tests</h2><small>{tests.length} tests</small></header><TestExplorer tests={tests} verification={verification ?? null} runtime={runtime} coverage={coverage} generationStatus={generation.generation_status} generationTimestamp={[...activities].reverse().find((event) => /generated|generation complete/i.test(`${event.label} ${event.detail}`))?.at ?? null} projectName={job.projectName} projectId={project?.id} onOpenRuntime={onRuntime} /></section>}
    </main>

    <footer className="console-actions">
      {generation && (
        <Button variant="secondary" onClick={onExport} style={{ display: 'inline-flex', alignItems: 'center', gap: '8px', borderRadius: '9999px', padding: '10px 22px', fontWeight: 700, fontSize: '12px' }}>
          <Download size={15} /> Export Tests
        </Button>
      )}
      {job.status === 'paused' ? (
        <Button
          onClick={onResume}
          style={{
            background: 'linear-gradient(to right, #FF602B, #4318FF)',
            color: '#ffffff',
            border: 'none',
            borderRadius: '9999px',
            padding: '10px 24px',
            fontWeight: 800,
            fontSize: '12px',
            boxShadow: '0 4px 16px rgba(255, 96, 43, 0.35)',
            display: 'inline-flex',
            alignItems: 'center',
            gap: '8px',
            cursor: 'pointer'
          }}
        >
          <Play size={15} /> Continue
        </Button>
      ) : generation && verification ? (
        <Button
          onClick={onRuntime}
          style={{
            background: 'linear-gradient(to right, #FF602B, #4318FF)',
            color: '#ffffff',
            border: 'none',
            borderRadius: '9999px',
            padding: '10px 24px',
            fontWeight: 800,
            fontSize: '12px',
            boxShadow: '0 4px 16px rgba(255, 96, 43, 0.35)',
            display: 'inline-flex',
            alignItems: 'center',
            gap: '8px',
            cursor: 'pointer'
          }}
        >
          <Play size={15} /> Run Runtime Validation
        </Button>
      ) : null}
    </footer>
  </section>
}
