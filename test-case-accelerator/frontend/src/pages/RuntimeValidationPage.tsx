import { useCallback, useEffect, useMemo, useRef, useState, type ReactNode } from 'react'
import { ArrowLeft, ArrowUpDown, CheckCircle2, Clipboard, Download, FileCode2, RefreshCw, RotateCcw, Search, SkipForward, Timer, XCircle } from 'lucide-react'
import { useNavigate, useParams } from 'react-router-dom'
import { api } from '../api/client'
import type { RuntimeExecutionResult, RuntimeTestStatus, RuntimeValidationReport, RuntimeValidationRun, RuntimeValidationStatus } from '../api/types'
import { Badge, Button, Empty, ErrorNotice } from '../components/ui'
import { useAppState } from '../state/app-state'

const DEFAULT_BASE_URL = 'http://127.0.0.1:8001'
const TERMINAL_STATUSES = new Set<RuntimeValidationStatus>(['completed', 'failed', 'partial', 'timed_out', 'cancelled'])
const MAX_POLL_FAILURES = 3

function statusTone(status?: RuntimeValidationStatus | RuntimeTestStatus) {
  if (status === 'completed' || status === 'Passed') return 'success' as const
  if (status === 'failed' || status === 'Failed' || status === 'timed_out') return 'danger' as const
  if (status === 'partial' || status === 'Skipped' || status === 'NotExecutable') return 'warning' as const
  return 'info' as const
}

function formatDuration(milliseconds?: number | null) {
  if (milliseconds == null) return 'Not available'
  if (milliseconds < 1000) return `${Math.round(milliseconds)} ms`
  return `${(milliseconds / 1000).toFixed(2)} s`
}

function validateBaseUrl(value: string) {
  try { const url = new URL(value); return url.protocol === 'http:' || url.protocol === 'https:' } catch { return false }
}

function exportJson(name: string, value: unknown) {
  const href = URL.createObjectURL(new Blob([JSON.stringify(value, null, 2)], { type: 'application/json' }))
  const anchor = document.createElement('a'); anchor.href = href; anchor.download = `${name}.json`; anchor.click(); URL.revokeObjectURL(href)
}

function saveCode(name: string, value: string) {
  const href = URL.createObjectURL(new Blob([value], { type: 'text/x-python' }))
  const anchor = document.createElement('a'); anchor.href = href; anchor.download = name; anchor.click(); URL.revokeObjectURL(href)
}

function pythonLine(line: string): ReactNode[] {
  return line.split(/(#.*$|"(?:\\.|[^"\\])*"|'(?:\\.|[^'\\])*'|\b(?:async|await|def|class|return|raise|with|as|if|elif|else|for|in|from|import|assert|try|except|True|False|None)\b)/g).filter(Boolean).map((token, index) => {
    const type = token.startsWith('#') ? 'comment' : token.startsWith('"') || token.startsWith("'") ? 'string' : /^(async|await|def|class|return|raise|with|as|if|elif|else|for|in|from|import|assert|try|except|True|False|None)$/.test(token) ? 'keyword' : ''
    return type ? <span className={`syntax-${type}`} key={index}>{token}</span> : <span key={index}>{token}</span>
  })
}

function failureReason(result: RuntimeExecutionResult) {
  if (result.runtime_status === 'Passed') return 'Passed'
  if (result.runtime_status === 'Skipped') return 'Skipped'
  if (result.runtime_status === 'NotExecutable') return 'Not executable'
  const text = `${result.assertion_failure ?? ''} ${JSON.stringify(result.actual_result ?? {})} ${result.logs ?? ''}`
  const http = text.match(/(?:HTTP|status(?: code)?)\s*[:=]?\s*(5\d\d|4\d\d)/i)
  if (http) return `HTTP ${http[1]}`
  for (const name of ['TimeoutError', 'Timeout', 'AttributeError', 'ImportError', 'ModuleNotFoundError', 'TypeError', 'ValueError', 'KeyError']) if (text.includes(name)) return name
  return result.assertion_failure ? 'Assertion Failed' : 'Runtime Failure'
}

type SortKey = 'status' | 'name' | 'duration'
type ResultFilter = 'all' | RuntimeTestStatus

export function RuntimeValidationPage() {
  const { id = '' } = useParams()
  const navigate = useNavigate()
  const state = useAppState()
  const understandingRunId = state.artifacts.understanding?.run_id
  const project = state.projects.find((item) => item.id === id)
  const generation = state.artifacts.generation
  const [baseUrl, setBaseUrl] = useState(DEFAULT_BASE_URL)
  const [run, setRun] = useState<RuntimeValidationRun | null>(null)
  const [report, setReport] = useState<RuntimeValidationReport | null>(null)
  const [starting, setStarting] = useState(false)
  const [polling, setPolling] = useState(false)
  const [pollFailures, setPollFailures] = useState(0)
  const [error, setError] = useState('')
  const [resultQuery, setResultQuery] = useState('')
  const [resultFilter, setResultFilter] = useState<ResultFilter>('all')
  const [sortKey, setSortKey] = useState<SortKey>('status')
  const [sortAscending, setSortAscending] = useState(true)
  const [selectedResultId, setSelectedResultId] = useState('')
  const timerRef = useRef<number | undefined>(undefined)
  const detailsRef = useRef<HTMLDivElement>(null)

  useEffect(() => { if (id && state.activeProjectId !== id) state.setActiveProjectId(id) }, [id, state.activeProjectId, state.setActiveProjectId])
  useEffect(() => () => { if (timerRef.current !== undefined) window.clearTimeout(timerRef.current) }, [])

  const loadReport = useCallback(async (runId: string) => {
    try { setReport(await api.runtimeValidationReport(runId)) }
    catch (reason) { setError(reason instanceof Error ? `The run finished, but its report could not be loaded: ${reason.message}` : 'The runtime report could not be loaded.') }
  }, [])

  const pollRun = useCallback(async (runId: string) => {
    if (timerRef.current !== undefined) window.clearTimeout(timerRef.current)
    setPolling(true)
    try {
      const nextRun = await api.runtimeValidation(runId)
      setRun(nextRun); setPollFailures(0); setError('')
      if (TERMINAL_STATUSES.has(nextRun.status)) { setPolling(false); await loadReport(runId); return }
      timerRef.current = window.setTimeout(() => void pollRun(runId), 2000)
    } catch (reason) {
      setPollFailures((current) => { const next = current + 1; if (next < MAX_POLL_FAILURES) timerRef.current = window.setTimeout(() => void pollRun(runId), 2000); else { setPolling(false); setError(reason instanceof Error ? `Status updates paused after ${MAX_POLL_FAILURES} attempts: ${reason.message}` : 'Status updates are temporarily unavailable.') } return next })
    }
  }, [loadReport])

  useEffect(() => { const runId = sessionStorage.getItem(`testforge-runtime-run:${id}`); if (runId) void pollRun(runId) }, [id, pollRun])

  const start = async () => {
    const normalizedUrl = baseUrl.trim().replace(/\/$/, '')
    if (!validateBaseUrl(normalizedUrl)) { setError('Enter a valid HTTP or HTTPS base URL.'); return }
    if (!understandingRunId) { setError('Repository analysis must complete before runtime validation can run.'); return }
    setStarting(true); setError(''); setReport(null); setRun(null); setPollFailures(0); setSelectedResultId('')
    try { const nextRun = await api.startRuntimeValidation(id, understandingRunId, normalizedUrl); setRun(nextRun); if (TERMINAL_STATUSES.has(nextRun.status)) await loadReport(nextRun.run_id); else await pollRun(nextRun.run_id) }
    catch (reason) { setError(reason instanceof Error ? reason.message : 'Runtime validation could not be started. Confirm that the target application is reachable and try again.') }
    finally { setStarting(false) }
  }

  const summary = report?.summary ?? run?.summary
  const busy = starting || polling
  const tests = generation?.generated_test_cases ?? []
  const testById = useMemo(() => new Map(tests.map((test) => [test.id, test])), [tests])
  const executed = summary ? summary.passed + summary.failed + summary.skipped + summary.not_executable : null
  const progress = summary?.total ? Math.round((executed ?? 0) / summary.total * 100) : report ? 100 : null

  const displayedResults = useMemo(() => [...(report?.results ?? [])].filter((result) => {
    const test = testById.get(result.test_case_id)
    const target = String(test?.unit_test?.symbol ?? test?.traceability?.symbol ?? '')
    const haystack = `${result.test_case_id} ${test?.title ?? ''} ${target}`.toLowerCase()
    return (resultFilter === 'all' || result.runtime_status === resultFilter) && (!resultQuery || haystack.includes(resultQuery.toLowerCase()))
  }).sort((left, right) => {
    const compared = sortKey === 'duration' ? left.execution_time_ms - right.execution_time_ms : sortKey === 'name' ? (testById.get(left.test_case_id)?.title ?? left.test_case_id).localeCompare(testById.get(right.test_case_id)?.title ?? right.test_case_id) : left.runtime_status.localeCompare(right.runtime_status)
    return sortAscending ? compared : -compared
  }), [report, resultFilter, resultQuery, sortAscending, sortKey, testById])

  const selectedResult = report?.results.find((item) => item.test_case_id === selectedResultId)
  const selectSort = (key: SortKey) => { if (sortKey === key) setSortAscending((value) => !value); else { setSortKey(key); setSortAscending(true) } }
  const actualField = (result: RuntimeExecutionResult | undefined, ...keys: string[]) => keys.map((key) => result?.actual_result?.[key]).find((value) => value != null)
  const detail = (value: unknown) => value == null || value === '' ? 'Not provided by runtime' : typeof value === 'string' ? value : JSON.stringify(value, null, 2)

  return <div className="page runtime-runner-page">
    <header className="runner-heading"><div><small>TestForge execution</small><h1>Runtime Validation</h1><p>{project ? `${project.name} · Execute the generated suite and inspect runtime evidence.` : 'Execute and inspect the generated unit test suite.'}</p></div>{report && <div><Button variant="secondary" onClick={() => navigate(`/ai-test-results/${id}/tests`)}><FileCode2 size={15} /> Generated Tests</Button><Button variant="secondary" onClick={() => exportJson(`${project?.name ?? 'project'}-runtime-results`, report)}><Download size={15} /> Export Results</Button></div>}</header>
    <section className="runner-target"><div><span className={`connection-dot ${run && run.status !== 'failed' ? 'connected' : ''}`} /><span><small>Target application</small><strong>{run && run.status !== 'failed' ? 'Connected' : 'Disconnected'}</strong></span></div><label htmlFor="runtime-base-url"><span>Base URL</span><input id="runtime-base-url" type="url" value={baseUrl} onChange={(event) => setBaseUrl(event.target.value)} disabled={busy} /></label><Button onClick={() => void start()} disabled={busy || !understandingRunId}>{busy ? <><RefreshCw size={15} /> Validation running</> : <><RotateCcw size={15} /> {report ? 'Run Validation Again' : 'Run Runtime Validation'}</>}</Button></section>
    {!understandingRunId && !state.artifactsLoading && <ErrorNotice message="Runtime validation is available after unit tests are generated and optimized for this project." />}
    {error && <div className="runtime-error"><ErrorNotice message={error} />{run && pollFailures >= MAX_POLL_FAILURES && <Button variant="secondary" onClick={() => { setError(''); setPollFailures(0); void pollRun(run.run_id) }}><RefreshCw size={15} /> Retry status updates</Button>}</div>}

    {busy && <section className="runner-progress" aria-live="polite"><header><div><span className="runtime-live-dot" /><span><small>Runtime validation</small><strong>{starting ? 'Starting execution' : 'Executing generated tests'}</strong></span></div>{run?.duration_ms != null && <span><Timer size={14} /> {formatDuration(run.duration_ms)}</span>}</header><div className={`progress-track ${progress == null ? 'indeterminate' : ''}`}><i style={progress == null ? undefined : { width: `${progress}%` }} /></div>{summary && <footer><span>{executed} / {summary.total} executed</span><strong>{progress}%</strong></footer>}</section>}

    {report && <section className="runner-summary"><article className="passed"><CheckCircle2 size={16} /><span>Passed<strong>{summary?.passed ?? 0}</strong></span></article><article className="failed"><XCircle size={16} /><span>Failed<strong>{summary?.failed ?? 0}</strong></span></article><article><SkipForward size={16} /><span>Skipped<strong>{summary?.skipped ?? 0}</strong></span></article><article><Timer size={16} /><span>Duration<strong>{formatDuration(report.duration_ms)}</strong></span></article><article><span>Pass Rate<strong>{summary?.pass_rate.toFixed(1)}%</strong></span></article><article><span>Total Executed<strong>{executed ?? 0}</strong></span></article></section>}

    {report && <section className="runner-results"><header><div><h2>Executed Tests</h2><p>Select a test to inspect its complete execution report.</p></div><div><label><Search size={14} /><input value={resultQuery} onChange={(event) => setResultQuery(event.target.value)} placeholder="Search tests or targets" /></label><select value={resultFilter} onChange={(event) => setResultFilter(event.target.value as ResultFilter)}><option value="all">All results</option><option value="Passed">Passed</option><option value="Failed">Failed</option><option value="Skipped">Skipped</option><option value="NotExecutable">Not executable</option></select></div></header>{report.results.length ? <div className="runner-table"><table><thead><tr><th><button onClick={() => selectSort('status')}>Status <ArrowUpDown size={11} /></button></th><th><button onClick={() => selectSort('name')}>Test Name <ArrowUpDown size={11} /></button></th><th>Target Function</th><th><button onClick={() => selectSort('duration')}>Execution Time <ArrowUpDown size={11} /></button></th><th>Failure Reason</th></tr></thead><tbody>{displayedResults.map((result) => { const test = testById.get(result.test_case_id); return <tr key={result.test_case_id} onClick={() => { setSelectedResultId(result.test_case_id); window.setTimeout(() => detailsRef.current?.focus(), 0) }}><td><Badge tone={statusTone(result.runtime_status)}>{result.runtime_status}</Badge></td><td><strong>{test?.title ?? result.test_case_id}</strong></td><td>{String(test?.unit_test?.symbol ?? test?.traceability?.symbol ?? 'Not provided')}</td><td>{formatDuration(result.execution_time_ms)}</td><td><span className={`failure-reason ${result.runtime_status.toLowerCase()}`}>{failureReason(result)}</span></td></tr> })}</tbody></table>{!displayedResults.length && <p>No results match the current filters.</p>}</div> : <Empty title="No executed tests" detail="The completed runtime report contains no individual test results." />}</section>}

    {selectedResult && (() => { const test = testById.get(selectedResult.test_case_id); const code = test?.unit_test?.generated_code ?? ''; const request = selectedResult.expected_result?.request ?? selectedResult.expected_result; const response = selectedResult.actual_result?.response ?? selectedResult.actual_result?.http_response ?? selectedResult.actual_result; return <section className="runtime-test-details" ref={detailsRef} tabIndex={-1}><header><button onClick={() => setSelectedResultId('')}><ArrowLeft size={15} /> Back to Executed Tests</button><div><small>Runtime Test Details</small><h1>{test?.title ?? selectedResult.test_case_id}</h1></div><Badge tone={statusTone(selectedResult.runtime_status)}>{selectedResult.runtime_status}</Badge></header><div className="runtime-detail-content"><details open><summary>Test Overview</summary><dl><div><dt>Status</dt><dd>{selectedResult.runtime_status}</dd></div><div><dt>Test Name</dt><dd>{test?.title ?? selectedResult.test_case_id}</dd></div>{test?.category && <div><dt>Category</dt><dd>{test.category}</dd></div>}<div><dt>Target Function</dt><dd>{String(test?.unit_test?.symbol ?? test?.traceability?.symbol ?? 'Not provided')}</dd></div><div><dt>Duration</dt><dd>{formatDuration(selectedResult.execution_time_ms)}</dd></div></dl></details><details open={selectedResult.runtime_status === 'Failed'}><summary>Failure Summary</summary><div className="runtime-detail-grid"><article><span>Expected Result</span><pre>{detail(selectedResult.expected_result)}</pre></article><article><span>Actual Result</span><pre>{detail(selectedResult.actual_result)}</pre></article><article><span>Failure Reason</span><pre>{detail(selectedResult.assertion_failure ?? failureReason(selectedResult))}</pre></article></div></details>{code && <details><summary>Generated Test Code</summary><div className="runtime-code-toolbar"><button onClick={() => void navigator.clipboard.writeText(code)}><Clipboard size={14} /> Copy</button><button onClick={() => saveCode(`test_${selectedResult.test_case_id}.py`, code)}><Download size={14} /> Download</button></div><div className="runtime-code"><ol>{code.split('\n').map((line, index) => { const highlighted = pythonLine(line); return <li key={index}><code>{highlighted.length ? highlighted : ' '}</code></li> })}</ol></div></details>}<details><summary>HTTP Request / Response</summary><div className="runtime-detail-grid"><article><span>Request</span><pre>{detail(request)}</pre></article><article><span>Response</span><pre>{detail(response)}</pre></article><article><span>Status Code</span><pre>{detail(actualField(selectedResult, 'status_code', 'http_status'))}</pre></article></div></details><details><summary>Stack Trace</summary><pre>{detail(actualField(selectedResult, 'traceback', 'stack_trace'))}</pre></details><details><summary>Runtime Logs</summary><pre>{detail(selectedResult.logs)}</pre></details><details><summary>AI Analysis</summary><div className="runtime-detail-grid"><article><span>Root Cause</span><pre>{detail(actualField(selectedResult, 'root_cause', 'suggested_cause'))}</pre></article><article><span>Suggested Fix</span><pre>{detail(actualField(selectedResult, 'suggested_fix', 'suggested_next_action', 'recommendation'))}</pre></article></div></details></div></section> })()}
  </div>
}
