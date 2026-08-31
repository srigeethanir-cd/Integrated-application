import { useEffect, useMemo, useState } from 'react'
import { ArrowLeft, CheckCircle2, ChevronDown, Clipboard, Download, FileCode2, Folder, Maximize2, Minimize2, Search, ShieldCheck, Sparkles } from 'lucide-react'
import { NavLink, useNavigate, useParams } from 'react-router-dom'
import type { TestCase } from '../api/types'
import { api } from '../api/client'
import { useAppState } from '../state/app-state'
import { Badge, Button, Empty, Loading } from '../components/ui'

const sourceFile = (test: TestCase) => String(test.unit_test?.file ?? test.traceability?.file ?? test.traceability?.source_file ?? '').replaceAll('\\', '/')
const symbol = (test: TestCase) => String(test.unit_test?.symbol ?? test.traceability?.symbol ?? test.traceability?.target ?? '')
const verificationFor = (test: TestCase, results: ReturnType<typeof useAppState>['artifacts']['verification']) => results?.results.find((item) => item.test_case_id === test.id)

function save(name: string, content: string, type = 'text/plain') {
  const href = URL.createObjectURL(new Blob([content], { type }))
  const anchor = document.createElement('a')
  anchor.href = href
  anchor.download = name
  anchor.click()
  URL.revokeObjectURL(href)
}

function pythonLine(line: string) {
  const tokens = line.split(/(#.*$|"(?:\\.|[^"\\])*"|'(?:\\.|[^'\\])*'|\b(?:async|await|def|class|return|raise|with|as|if|elif|else|for|in|from|import|assert|try|except|True|False|None)\b)/g).filter(Boolean)
  return tokens.map((token, index) => {
    const type = token.startsWith('#') ? 'comment' : token.startsWith('"') || token.startsWith("'") ? 'string' : /^(async|await|def|class|return|raise|with|as|if|elif|else|for|in|from|import|assert|try|except|True|False|None)$/.test(token) ? 'keyword' : ''
    return type ? <span className={`syntax-${type}`} key={index}>{token}</span> : <span key={index}>{token}</span>
  })
}

function ResultsNav({ projectId }: { projectId: string }) {
  return null
}

function useResultsProject() {
  const { id = '' } = useParams()
  const state = useAppState()
  useEffect(() => { if (id && state.activeProjectId !== id) state.setActiveProjectId(id) }, [id, state])
  return { id, state, project: state.projects.find((item) => item.id === id), job: state.jobs[id] }
}

export function AITestResultsOverview() {
  const { id, state, project, job } = useResultsProject()
  const generation = state.artifacts.generation
  const verification = state.artifacts.verification
  const quality = state.artifacts.quality
  const dependency = state.artifacts.dependency
  if (state.artifactsLoading) return <div className="page"><Loading /></div>
  if (!generation || !project) return <div className="page"><ResultsNav projectId={id} /><Empty title="AI Test Results are not ready" detail="Generate unit tests before opening this workspace." /></div>
  const coverage = Object.values(generation.coverage_summary).filter((value): value is number => typeof value === 'number')
  const coverageValue = coverage.length ? Math.round(coverage.reduce((sum, value) => sum + value, 0) / coverage.length) : null
  return <div className="page results-page"><ResultsNav projectId={id} /><header className="results-heading"><div><small>Generated test suite</small><h1>{project.name}</h1><p>Review generation, verification, and quality results before runtime validation or export.</p></div><Badge tone={verification?.summary.failed ? 'danger' : verification ? 'success' : 'info'}>{verification ? verification.summary.failed ? 'Needs review' : 'Verified' : generation.generation_status ?? 'Generated'}</Badge></header>
    <section className="results-summary-grid"><article><span>Generated tests</span><strong>{generation.total_after_deduplication}</strong></article>{verification && <><article><span>Verified</span><strong>{verification.summary.verified}</strong></article><article><span>Needs review</span><strong>{verification.summary.partial + verification.summary.failed}</strong></article></>}{coverageValue != null && <article><span>Coverage</span><strong>{coverageValue}%</strong></article>}{quality && <article><span>Quality score</span><strong>{quality.final_score}%</strong></article>}<article><span>Repository files</span><strong>{dependency?.files.length ?? 0}</strong></article></section>
    <div className="results-overview-grid"><section><h2>Repository summary</h2><dl><div><dt>Project</dt><dd>{project.name}</dd></div><div><dt>Source</dt><dd>{project.source_type}</dd></div>{dependency && <div><dt>Files analyzed</dt><dd>{dependency.files.length}</dd></div>}<div><dt>Tests generated</dt><dd>{generation.total_after_deduplication}</dd></div></dl></section>{quality && <section><h2>Quality metrics</h2><dl>{Object.entries(quality.quality_evaluation.dimension_scores).map(([name, value]) => <div key={name}><dt>{name.replaceAll('_', ' ')}</dt><dd>{value}%</dd></div>)}</dl></section>}<section className="results-activity"><h2>Recent activity</h2>{job?.timeline.slice(-6).reverse().map((event) => <article key={event.id}><CheckCircle2 size={14} /><span><strong>{event.label}</strong><small>{event.at.toLocaleString()}</small></span></article>) ?? <p>No activity was recorded.</p>}</section></div>
  </div>
}

export function AITestExplorerPage() {
  const { id, state, project } = useResultsProject()
  const navigate = useNavigate()
  const [query, setQuery] = useState('')
  const [filter, setFilter] = useState('All')
  const tests = state.artifacts.generation?.generated_test_cases ?? []
  const verification = state.artifacts.verification
  const filtered = useMemo(() => tests.filter((test) => (filter === 'All' || test.category === filter || verificationFor(test, verification)?.status === filter) && [test.title, sourceFile(test), symbol(test), test.category].join(' ').toLowerCase().includes(query.toLowerCase())), [filter, query, tests, verification])
  const groups = useMemo(() => Object.entries(filtered.reduce<Record<string, TestCase[]>>((all, test) => { const file = sourceFile(test) || 'Generated tests'; return { ...all, [file]: [...(all[file] ?? []), test] } }, {})).sort(([a], [b]) => a.localeCompare(b)), [filtered])
  const filters = ['All', ...new Set(tests.map((test) => test.category)), 'Verified', 'Partial', 'Failed']
  return <div className="page results-page"><ResultsNav projectId={id} /><header className="results-heading compact"><div><small>AI Test Results</small><h1>Test Explorer</h1><p>{project?.name} · {tests.length} generated tests</p></div><label className="results-search"><Search size={15} /><input aria-label="Search generated tests" value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Search files, functions, or tests" /></label></header><div className="explorer-filters">{filters.map((item) => <button key={item} className={filter === item ? 'active' : ''} onClick={() => setFilter(item)}>{item}</button>)}</div><section className="results-tree"><header><Folder size={16} /><strong>tests/</strong><span>{filtered.length}</span></header>{groups.length ? groups.map(([file, fileTests]) => <details open key={file}><summary><Folder size={15} /><span>{file}</span><small>{fileTests.length}</small></summary>{fileTests.map((test) => { const status = verificationFor(test, verification)?.status; return <button key={test.id} onClick={() => navigate(`/ai-test-results/${id}/tests/${encodeURIComponent(test.id)}`)}><FileCode2 size={15} /><span><strong>{test.title}</strong><small>{symbol(test)}</small></span>{status && <Badge tone={status === 'Verified' ? 'success' : status === 'Failed' ? 'danger' : 'warning'}>{status}</Badge>}</button> })}</details>) : <Empty title="No matching tests" detail="Adjust the search or verification filter." />}</section></div>
}

export function AITestDetailsPage() {
  const { id, state } = useResultsProject()
  const { testId = '' } = useParams()
  const navigate = useNavigate()
  const [copied, setCopied] = useState(false)
  const [codeOpen, setCodeOpen] = useState(false)
  const [fullscreen, setFullscreen] = useState(false)
  const test = state.artifacts.generation?.generated_test_cases.find((item) => item.id === decodeURIComponent(testId))
  const verification = test ? verificationFor(test, state.artifacts.verification) : undefined
  if (!test) return <div className="page results-page"><ResultsNav projectId={id} /><Empty title="Test not found" detail="The selected generated test is unavailable." /></div>
  const code = test.unit_test?.generated_code ?? ''
  const dependencies = [...new Set([...(test.unit_test?.patches ?? []), ...(test.unit_test?.fixture_names ?? []), ...(test.unit_test?.parameters ?? [])])]
  const coverage = [...new Set([test.category, test.unit_test?.patches?.length ? 'Dependency Mocking' : null, test.expected_results.length ? 'Assertions' : null, test.unit_test?.expected_exception ? 'Exception' : null].filter((item): item is string => Boolean(item)))]
  const copyCode = async () => { await navigator.clipboard.writeText(code); setCopied(true); window.setTimeout(() => setCopied(false), 1200) }
  return <div className="page results-page test-documentation-page"><ResultsNav projectId={id} />
    <button className="test-back" onClick={() => navigate(`/ai-test-results/${id}/tests`)}><ArrowLeft size={15} /> Back to Test Explorer</button>
    <header className="test-detail-heading"><div><div className="test-detail-labels"><Badge tone="info">{test.category}</Badge>{verification && <Badge tone={verification.status === 'Verified' ? 'success' : verification.status === 'Failed' ? 'danger' : 'warning'}>{verification.status}</Badge>}</div><h1>{test.title}</h1><p>{sourceFile(test)}{symbol(test) ? ` · ${symbol(test)}` : ''}</p></div><div><Button variant="secondary" onClick={() => void copyCode()}><Clipboard size={15} /> {copied ? 'Copied' : 'Copy'}</Button><Button variant="secondary" onClick={() => save(`test_${test.id}.py`, code, 'text/x-python')}><Download size={15} /> Download</Button></div></header>

    <section className="test-purpose"><div className="test-purpose-icon"><Sparkles size={19} /></div><div><small>Test purpose</small><h2>{test.description || test.title}</h2><dl>{symbol(test) && <div><dt>Target function</dt><dd>{symbol(test)}</dd></div>}{sourceFile(test) && <div><dt>Source file</dt><dd>{sourceFile(test)}</dd></div>}<div><dt>Generated by</dt><dd>TestForge AI</dd></div></dl></div></section>

    {coverage.length > 0 && <section className="test-document-section"><header><h2>Coverage</h2><p>Behaviors represented by the generated test metadata.</p></header><div className="test-coverage-chips">{coverage.map((item) => <span key={item}><CheckCircle2 size={14} /> {item}</span>)}</div></section>}
    {dependencies.length > 0 && <section className="test-document-section"><header><h2>Dependencies</h2><p>Fixtures, parameters, and patched collaborators used by this test.</p></header><div className="test-readable-list">{dependencies.map((item) => <article key={item}><ShieldCheck size={15} /><span>{item}</span></article>)}</div></section>}
    {test.expected_results.length > 0 && <section className="test-document-section"><header><h2>Assertions</h2><p>Expected behavior captured by the generated test.</p></header><div className="test-readable-list assertions">{test.expected_results.map((item) => <article key={item}><CheckCircle2 size={15} /><code>{item}</code></article>)}</div></section>}
    {verification && <section className="test-document-section"><header><h2>Verification</h2><p>Evidence used to verify this generated unit test.</p></header><div className="test-verification-summary"><Badge tone={verification.status === 'Verified' ? 'success' : verification.status === 'Failed' ? 'danger' : 'warning'}>{verification.status}</Badge><span>{Math.round(verification.confidence * (verification.confidence <= 1 ? 100 : 1))}% confidence</span><span>{verification.verification_path}</span></div>{verification.evidence.length > 0 && <details className="test-evidence"><summary>View evidence <span>{verification.evidence.length}</span></summary><ul>{verification.evidence.map((item, index) => <li key={index}><strong>{item.file}{item.line ? `:${item.line}` : ''}</strong><p>{item.detail}</p></li>)}</ul></details>}</section>}

    <section className={`generated-code-section ${fullscreen ? 'fullscreen' : ''}`}><button className="generated-code-toggle" onClick={() => setCodeOpen((open) => !open)} aria-expanded={codeOpen}><span><FileCode2 size={17} /><span><strong>Generated Code</strong><small>Review the executable pytest implementation.</small></span></span><span>View Generated Code <ChevronDown size={16} /></span></button>{codeOpen && <div className="generated-code-body"><header><span>pytest · read only</span><div><button onClick={() => void copyCode()}><Clipboard size={14} /> {copied ? 'Copied' : 'Copy'}</button><button onClick={() => save(`test_${test.id}.py`, code, 'text/x-python')}><Download size={14} /> Download</button><button onClick={() => setFullscreen((value) => !value)}>{fullscreen ? <Minimize2 size={14} /> : <Maximize2 size={14} />} {fullscreen ? 'Exit Fullscreen' : 'Fullscreen'}</button></div></header><div className="test-detail-editor" aria-label="Generated pytest code"><ol>{code.split('\n').map((line, index) => { const highlighted = pythonLine(line); return <li key={index}><code>{highlighted.length ? highlighted : ' '}</code></li> })}</ol></div></div>}</section>
  </div>
}

export function AITestExportPage() {
  const { id, state, project } = useResultsProject()
  const [exporting, setExporting] = useState(false)
  const generation = state.artifacts.generation
  const verification = state.artifacts.verification
  const quality = state.artifacts.quality
  const downloadZip = async () => { setExporting(true); try { const blob = await api.exportTestSuite(id); const href = URL.createObjectURL(blob); const anchor = document.createElement('a'); anchor.href = href; anchor.download = 'test-suite.zip'; anchor.click(); URL.revokeObjectURL(href) } finally { setExporting(false) } }
  const report = { project: project?.name, generation, verification, quality }
  const junit = `<?xml version="1.0" encoding="UTF-8"?><testsuite name="${project?.name ?? 'TestForge'}" tests="${generation?.total_after_deduplication ?? 0}" failures="${verification?.summary.failed ?? 0}"></testsuite>`
  return <div className="page results-page"><ResultsNav projectId={id} /><header className="results-heading"><div><small>AI Test Results</small><h1>Export Test Suite</h1><p>Download generated artifacts for {project?.name}.</p></div></header>{generation ? <section className="export-options"><button onClick={() => void downloadZip()} disabled={exporting}><Download size={20} /><strong>Export ZIP</strong><span>Production-ready pytest project</span></button><button onClick={() => void downloadZip()} disabled={exporting}><FileCode2 size={20} /><strong>Pytest package</strong><span>Complete executable test suite</span></button><button onClick={() => save(`${project?.name}-tests.json`, JSON.stringify(report, null, 2), 'application/json')}><Download size={20} /><strong>JSON</strong><span>Generation and verification artifacts</span></button><button onClick={() => save(`${project?.name}-report.html`, `<html><body><pre>${JSON.stringify(report, null, 2).replaceAll('&', '&amp;').replaceAll('<', '&lt;')}</pre></body></html>`, 'text/html')}><ShieldCheck size={20} /><strong>HTML report</strong><span>Portable results report</span></button><button onClick={() => save(`${project?.name}-junit.xml`, junit, 'application/xml')}><Download size={20} /><strong>JUnit XML</strong><span>CI-compatible suite summary</span></button></section> : <Empty title="Nothing to export" detail="Generate unit tests before opening the export center." />}</div>
}
