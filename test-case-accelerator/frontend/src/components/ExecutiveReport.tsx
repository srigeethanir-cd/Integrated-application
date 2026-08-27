import { useEffect, useMemo, useState } from 'react'
import { AlertTriangle, CheckCircle2, Download, FileArchive, FileCode2, FileText, Gauge, RefreshCw, ShieldCheck, Sparkles, TestTube2 } from 'lucide-react'
import { useNavigate } from 'react-router-dom'
import { api } from '../api/client'
import type { RuntimeValidationReport, TestCase } from '../api/types'
import { Badge, Button, Empty, ErrorNotice, Loading } from './ui'
import { useAppState } from '../state/app-state'

const formatDuration = (milliseconds?: number | null) => milliseconds == null ? 'Not available' : milliseconds < 1000 ? `${Math.round(milliseconds)} ms` : `${(milliseconds / 1000).toFixed(2)} s`
const categoryCount = (tests: TestCase[], pattern: RegExp) => tests.filter((test) => pattern.test([test.category, test.title, test.description].join(' '))).length

function downloadText(name: string, content: string, type = 'text/x-python') {
  const blob = new Blob([content], { type: `${type};charset=utf-8` })
  const href = URL.createObjectURL(blob)
  const anchor = document.createElement('a')
  anchor.href = href
  anchor.download = name
  anchor.click()
  URL.revokeObjectURL(href)
}

export function ExecutiveReport() {
  const state = useAppState()
  const navigate = useNavigate()
  const project = state.projects.find((item) => item.id === state.activeProjectId)
  const generation = state.artifacts.generation
  const verification = state.artifacts.verification
  const quality = state.artifacts.quality
  const [runtime, setRuntime] = useState<RuntimeValidationReport | null>(null)
  const [runtimeLoading, setRuntimeLoading] = useState(false)
  const [runtimeError, setRuntimeError] = useState('')

  useEffect(() => {
    if (!project) { setRuntime(null); return }
    const runId = sessionStorage.getItem(`testforge-runtime-run:${project.id}`)
    if (!runId) { setRuntime(null); return }
    setRuntimeLoading(true); setRuntimeError('')
    void api.runtimeValidationReport(runId).then(setRuntime).catch((reason) => setRuntimeError(reason instanceof Error ? reason.message : 'Runtime report unavailable.')).finally(() => setRuntimeLoading(false))
  }, [project?.id])

  const tests = quality?.optimized_test_suite?.length ? quality.optimized_test_suite : generation?.generated_test_cases ?? []
  const verified = verification?.summary.verified ?? 0
  const needsReview = verification ? verification.summary.partial + verification.summary.failed : null
  const coverage = quality?.quality_evaluation.dimension_scores.coverage ?? generation?.coverage_summary.unit_target_coverage ?? generation?.coverage_summary.function_coverage ?? generation?.coverage_summary.requirement_coverage
  const confidence = verification?.results.length ? Math.round(verification.results.reduce((sum, item) => sum + (item.confidence <= 1 ? item.confidence * 100 : item.confidence), 0) / verification.results.length) : null
  const findings = verification?.results.flatMap((result) => result.findings) ?? []
  const ruleCompliance = findings.length ? Math.round(findings.filter((finding) => finding.status === 'Verified').length / findings.length * 100) : null
  const warnings = findings.filter((finding) => finding.status !== 'Verified').length
  const runtimeReady = Boolean(runtime && runtime.summary.total > 0 && runtime.summary.failed === 0 && runtime.summary.not_executable === 0)
  const qualityReady = Boolean(quality?.quality_evaluation.threshold_met)
  const verificationReady = Boolean(verification && verification.summary.failed === 0 && verification.summary.partial === 0)
  const productionReady = runtimeReady && qualityReady && verificationReady
  const needsRegeneration = Boolean(quality && !quality.quality_evaluation.threshold_met)
  const recommendation = productionReady ? 'Ready for Production' : needsRegeneration ? 'Needs Regeneration' : 'Needs Review'
  const recommendationTone = productionReady ? 'success' : needsRegeneration ? 'danger' : 'warning'
  const generationJob = project ? state.jobs[project.id] : undefined
  const generationDuration = generationJob?.logs?.find((line) => line.startsWith('Stage 4 generation duration:'))?.split(':').slice(1).join(':').trim() ?? 'Not available'
  const generatedPytest = tests.map((test) => test.unit_test?.generated_code).filter((code): code is string => Boolean(code)).join('\n\n')

  const analysis = [
    ['Positive Tests', categoryCount(tests, /^positive\b/i)],
    ['Negative Tests', categoryCount(tests, /^negative\b/i)],
    ['Boundary Tests', categoryCount(tests, /boundary|edge.?case/i)],
    ['Exception Tests', categoryCount(tests, /exception/i)],
    ['Regression Tests', categoryCount(tests, /regression/i)],
    ['Parameterized Tests', tests.filter((test) => /@pytest\.mark\.parametrize/.test(test.unit_test?.generated_code ?? '')).length],
    ['Mock-based Tests', tests.filter((test) => Boolean(test.unit_test?.patches.length) || /MagicMock|AsyncMock|\bpatch\b/.test(test.unit_test?.generated_code ?? '')).length],
    ['Security Tests', categoryCount(tests, /security/i)],
  ] as const
  const largestCategory = Math.max(1, ...analysis.map(([, count]) => count))

  const recommendations = useMemo(() => {
    const items = [...(quality?.quality_evaluation.recommendations ?? [])]
    const missing = quality?.quality_evaluation.feedback.missing_categories
    if (Array.isArray(missing)) missing.filter((item): item is string => typeof item === 'string').forEach((item) => items.push(`Increase ${item.replaceAll('_', ' ')} coverage.`))
    if (!runtime) items.push('Runtime validation is missing; execute the generated suite before production approval.')
    else if (runtime.summary.failed) items.push(`Review ${runtime.summary.failed} failed runtime test${runtime.summary.failed === 1 ? '' : 's'}.`)
    if (!verification) items.push('Verification is pending.')
    else if (verification.summary.partial || verification.summary.failed) items.push(`Review ${verification.summary.partial + verification.summary.failed} tests that are not fully verified.`)
    return [...new Set(items)]
  }, [quality, runtime, verification])

  if (state.artifactsLoading) return <Loading label="Loading executive report…" />
  if (!project) return <Empty title="Choose a project" detail="Select a project to view its production-readiness report." action={<Button onClick={() => navigate('/projects')}>Open Projects</Button>} />
  if (!generation || !verification || !quality) return <Empty title="Report not ready" detail="Generation, verification, and quality optimization must complete before the executive report is available." action={<Button onClick={() => navigate(`/processing/${project.id}`)}>Open Generate Tests</Button>} />

  return <div className="executive-report">
    <section className="report-hero"><div><small>Executive Test Quality Report</small><h1>{project.name}</h1><p>Is this generated test suite ready for production?</p></div><div className="report-hero-score"><span>Overall Quality<strong>{quality.final_score}%</strong></span><span>Runtime Readiness<strong>{runtimeLoading ? 'Loading…' : runtime ? runtimeReady ? 'Ready' : 'Needs review' : 'Not validated'}</strong></span><span>Generation Status<strong>{generation.generation_status ?? 'Complete'}</strong></span></div><div className={`report-recommendation ${recommendationTone}`}><span>{productionReady ? <CheckCircle2 /> : needsRegeneration ? <RefreshCw /> : <AlertTriangle />}</span><div><small>Overall recommendation</small><strong>{recommendation}</strong></div></div></section>
    {runtimeError && <ErrorNotice message={`Runtime evidence could not be loaded: ${runtimeError}`} />}

    <section className="executive-section"><header><div><TestTube2 /><span><h2>Generation Summary</h2><p>Final suite output and validation totals.</p></span></div></header><div className="executive-metrics"><span>Generated Tests<strong>{tests.length}</strong></span><span>Verified Tests<strong>{verified}</strong></span><span>Needs Review<strong>{needsReview ?? 'Not available'}</strong></span><span>Runtime Passed<strong>{runtime?.summary.passed ?? 'Not validated'}</strong></span><span>Runtime Failed<strong>{runtime?.summary.failed ?? 'Not validated'}</strong></span><span>Coverage Estimate<strong>{coverage == null ? 'Not available' : `${Math.round(coverage)}%`}</strong></span><span>Generation Duration<strong>{generationDuration}</strong></span></div></section>

    <section className="executive-section"><header><div><Gauge /><span><h2>Quality Analysis</h2><p>Distribution of executable test strategies in the final suite.</p></span></div></header><div className="quality-analysis-list">{analysis.map(([label, count]) => <div key={label}><span>{label}</span><strong>{count}</strong><div><i style={{ width: `${count / largestCategory * 100}%` }} /></div></div>)}</div></section>

    <div className="executive-two-column"><section className="executive-section"><header><div><ShieldCheck /><span><h2>Verification Summary</h2><p>Static and semantic verification evidence.</p></span></div></header><dl className="executive-detail-list"><div><dt>Verification Status</dt><dd>{verificationReady ? 'Verified' : 'Needs review'}</dd></div><div><dt>Verification Confidence</dt><dd>{confidence == null ? 'Not available' : `${confidence}%`}</dd></div><div><dt>Rule Compliance</dt><dd>{ruleCompliance == null ? 'Not available' : `${ruleCompliance}%`}</dd></div><div><dt>Warnings</dt><dd>{warnings}</dd></div></dl></section>
      <section className="executive-section"><header><div><CheckCircle2 /><span><h2>Runtime Validation Summary</h2><p>Ground-truth pytest execution results.</p></span></div></header><dl className="executive-detail-list"><div><dt>Validation Status</dt><dd>{runtimeLoading ? 'Loading…' : runtime?.status ?? 'Not validated'}</dd></div><div><dt>Pass Rate</dt><dd>{runtime ? `${runtime.pass_rate.toFixed(1)}%` : 'Not available'}</dd></div><div><dt>Execution Duration</dt><dd>{formatDuration(runtime?.duration_ms)}</dd></div><div><dt>Failed Tests</dt><dd>{runtime?.summary.failed ?? 'Not available'}</dd></div><div><dt>Skipped Tests</dt><dd>{runtime?.summary.skipped ?? 'Not available'}</dd></div><div><dt>Overall Runtime Readiness</dt><dd>{runtime ? runtimeReady ? 'Ready' : 'Needs review' : 'Not validated'}</dd></div></dl></section></div>

    <section className="executive-section"><header><div><Sparkles /><span><h2>AI Recommendations</h2><p>Actions derived from persisted evaluation and validation evidence.</p></span></div></header>{recommendations.length ? <ol className="executive-recommendations">{recommendations.map((item) => <li key={item}>{item}</li>)}</ol> : <div className="report-positive"><CheckCircle2 /><span><strong>No outstanding recommendations</strong><small>The backend evaluation returned no remaining actions.</small></span></div>}</section>

    <section className="executive-section export-center"><header><div><Download /><span><h2>Export Center</h2><p>Available production artifacts and formats.</p></span></div></header><div><button disabled={!generatedPytest} onClick={() => downloadText(`${project.name}-pytest-suite.py`, generatedPytest)}><FileCode2 /><span><strong>Pytest Suite</strong><small>{generatedPytest ? 'Available' : 'Unavailable'}</small></span><Badge tone={generatedPytest ? 'success' : 'warning'}>{generatedPytest ? 'Ready' : 'Unavailable'}</Badge></button><button disabled><FileArchive /><span><strong>ZIP Archive</strong><small>Not provided by backend</small></span><Badge tone="warning">Unavailable</Badge></button><button disabled><FileText /><span><strong>JUnit XML</strong><small>Not exposed by runtime API</small></span><Badge tone="warning">Unavailable</Badge></button><button disabled><FileText /><span><strong>HTML Report</strong><small>Not provided by backend</small></span><Badge tone="warning">Unavailable</Badge></button><button disabled><FileText /><span><strong>Markdown Report</strong><small>Not provided by backend</small></span><Badge tone="warning">Unavailable</Badge></button></div></section>
  </div>
}
