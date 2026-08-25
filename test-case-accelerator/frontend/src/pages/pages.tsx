import { useEffect, useRef, useState, type CSSProperties, type ReactNode } from 'react'
import { ArrowRight, BarChart3, BrainCircuit, CheckCircle2, ChevronDown, ChevronUp, CircleAlert, Clipboard, Clock3, Code2, Download, Eye, FileArchive, FolderGit2, Gauge, GitBranch, History as HistoryIcon, Layers3, Lightbulb, RefreshCw, Search, ShieldCheck, Sparkles, Target, TestTube2, Trash2, TrendingUp, Upload, X } from 'lucide-react'
import { useNavigate, useParams } from 'react-router-dom'
import { api, securityScanErrorMessage } from '../api/client'
import type { RuntimeValidationReport, TestCase } from '../api/types'
import { Badge, Button, Empty, ErrorNotice, Loading, MetricCard, PageHeader, Section } from '../components/ui'
import { TestExplorer } from '../components/TestExplorer'
import { ExecutiveReport } from '../components/ExecutiveReport'
import { ProjectOverview } from '../components/ProjectOverview'
import { GenerateWorkspace } from '../components/GenerateWorkspace'
import { SecurityReview } from '../components/SecurityReview'
import { useAppState } from '../state/app-state'

const tone = (status?: string) => status === 'Verified' || status === 'READY' || status === 'complete' ? 'success' : status === 'Failed' || status === 'FAILED' || status === 'failed' ? 'danger' : status === 'Partial' || status === 'PROCESSING' ? 'warning' : 'info'

function testGroup(test: TestCase) {
  const traceability = test.traceability
  for (const key of ['module', 'feature', 'component']) {
    const value = traceability?.[key]
    if (typeof value === 'string' && value.trim()) return value
  }
  return test.category
}

function confidenceLabel(value?: number) {
  if (value == null) return { label: 'Pending review', tone: 'neutral' as const, level: 0 }
  if (value >= 0.85) return { label: 'Strong confidence', tone: 'success' as const, level: 3 }
  if (value >= 0.65) return { label: 'Good confidence', tone: 'info' as const, level: 2 }
  return { label: 'Needs review', tone: 'warning' as const, level: 1 }
}

function ResultSkeleton() {
  return <div className="skeleton-grid" aria-label="Loading saved results">{[0, 1, 2].map((item) => <div className="skeleton-card" key={item}><i /><span /><span /></div>)}</div>
}

function download(name: string, data: unknown) {
  const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  const anchor = document.createElement('a')
  anchor.href = url
  anchor.download = `${name}.json`
  anchor.click()
  URL.revokeObjectURL(url)
}

function downloadText(name: string, value: string) {
  const url = URL.createObjectURL(new Blob([value], { type: 'text/x-python' }))
  const link = document.createElement('a')
  link.href = url
  link.download = `${name}.py`
  link.click()
  URL.revokeObjectURL(url)
}

async function downloadTestSuite(projectId: string) {
  const blob = await api.exportTestSuite(projectId)
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = 'test-suite.zip'
  link.click()
  URL.revokeObjectURL(url)
}

function stage3ItemLabel(group: string, item: object, index: number) {
  const value = item as Record<string, unknown>
  if (group === 'Endpoints') return `${String(value.method ?? '')} ${String(value.route ?? '')}`.trim()
  if (group === 'Request Models') return `${String(value.request_model ?? value.request_type ?? `Request ${index + 1}`)} (${projectRelativePath(value.file)})`
  if (group === 'Response Models') return `${String(value.response_model ?? value.response_type ?? `Response ${index + 1}`)} (${projectRelativePath(value.file)})`
  if (group === 'Exceptions') {
    if (typeof value.name === 'string') return value.name
    const exceptions = value.exceptions
    return Array.isArray(exceptions) ? exceptions.join(', ') : `Exception ${index + 1}`
  }
  if (group === 'Semgrep Findings') return String(value.rule_id ?? value.message ?? `Finding ${index + 1}`)
  const label = String(value.qualified_name ?? value.name ?? value.module ?? value.path ?? value.symbol ?? `Item ${index + 1}`)
  return group === 'Functions' ? `${label} (${projectRelativePath(value.file)})` : label
}

function projectRelativePath(value: unknown): string {
  if (typeof value !== 'string' || !value) return unavailable
  const normalized = value.replaceAll('\\', '/')
  const marker = '/source/'
  return normalized.includes(marker) ? normalized.split(marker).at(-1) ?? normalized : normalized.replace(/^source\//, '')
}

function flattenExceptions(value: unknown): string[] {
  if (Array.isArray(value)) return value.flatMap(flattenExceptions)
  if (typeof value !== 'string') return []
  return value.split(',').map((item) => item.trim()).filter(Boolean)
}

function isRepositoryTestFile(value: unknown): boolean {
  const path = projectRelativePath(value).toLowerCase()
  const parts = path.split('/')
  const file = parts.at(-1) ?? ''
  return parts.some((part) => part === 'test' || part === 'tests' || part === 'spec' || part === 'specs')
    || file.startsWith('test_')
    || file.includes('.test.')
    || file.includes('.spec.')
}

function stringValues(value: unknown): string[] {
  return Array.isArray(value) ? value.map(String).filter(Boolean) : []
}

function symbolName(value: unknown): string {
  return String(value ?? '').split('.').at(-1) ?? ''
}

function patchLabel(value: string): string {
  const normalized = value.toLowerCase()
  if (/jwt|encode|decode|token/.test(normalized)) return 'JWT encoder'
  if (/password|verify_password|hash/.test(normalized)) return 'Password verifier'
  if (/session|get_db|database|\bdb\b/.test(normalized)) return 'Database session'
  if (/repository|repo/.test(normalized)) return 'Repository'
  if (/\b(copy|update)\b/.test(normalized)) return 'Repository'
  if (/utcnow|datetime|clock|\btime\b/.test(normalized)) return 'Clock'
  if (/uploadfile|upload_file/.test(normalized)) return 'UploadFile'
  if (/path|file|open|unlink|remove/.test(normalized)) return 'Filesystem'
  if (/client|request|http/.test(normalized)) return 'HTTP client'
  if (/depend|override/.test(normalized)) return 'Dependency injection'
  return value
}

function generatedCodeIndicators(code: string, category: string, isAsync: boolean) {
  return {
    mocks: /\b(MagicMock|AsyncMock|Mock|monkeypatch|patch)\b/.test(code),
    assertions: /\bassert\b/.test(code),
    exception: /pytest\.raises|exception/i.test(code) || /exception/i.test(category),
    boundary: /boundary/i.test(category),
    security: /security/i.test(category),
    async: isAsync || /async\s+def|await\s+/.test(code),
    parameterized: /parametrize/.test(code),
  }
}

function verificationRecommendation(check: string): string {
  if (check === 'duplicate') return 'Merge only semantically equivalent tests that target the same production symbol, behavior, and category.'
  if (/assert|behavior|return/.test(check)) return 'Align the generated assertion with the cited source behavior.'
  if (/source|file|symbol|evidence/.test(check)) return 'Resolve the source target and provide direct file and symbol evidence.'
  if (/dependency|import/.test(check)) return 'Correct the dependency or import target using the source contract.'
  if (/exception/.test(check)) return 'Align the expected exception with the repository analysis.'
  return `Review ${check.replaceAll('_', ' ')} using the cited deterministic evidence.`
}

const unavailable = 'Not Available'

function displayArtifact(value: unknown): string {
  if (value == null || value === '') return unavailable
  if (Array.isArray(value)) return value.length ? value.join(', ') : 'None detected'
  if (typeof value === 'object') return JSON.stringify(value)
  return String(value)
}

function readableRuleName(ruleId: string): string {
  const raw = ruleId.split('.').at(-1) ?? ruleId
  return raw.split(/[-_]/).filter((part) => !['python', 'security', 'rule'].includes(part.toLowerCase())).map((part) => part.toLowerCase() === 'jwt' ? 'JWT' : part.charAt(0).toUpperCase() + part.slice(1)).join(' ')
}

function findingRecommendation(metadata: Record<string, unknown>, message: string): unknown {
  const native = metadataValue(metadata, '_testforge_native_remediation')
  if (native) return native
  const direct = metadataValue(metadata, 'recommendation', 'remediation', 'fix')
  if (direct) return direct
  const consider = message.match(/\bConsider\s+(.+?)(?:\r?\n|$)/i)?.[1]?.trim()
  if (!consider) return undefined
  if (/jwt/i.test(message) && /hardcod/i.test(message) && /environment variable/i.test(consider)) {
    return 'Move the JWT secret into environment variables or another secure secret-management mechanism instead of hardcoding credentials.'
  }
  return `Consider ${consider}`
}

function metadataValue(
  value: Record<string, unknown> | undefined,
  ...keys: string[]
): unknown {
  if (!value) return undefined
  for (const key of keys) {
    if (value[key] != null && value[key] !== '') return value[key]
  }
  return undefined
}

function ArtifactField({ label, value }: { label: string; value: unknown }) {
  return <div><dt>{label}</dt><dd>{displayArtifact(value)}</dd></div>
}

function ActiveProjectGate({ children }: { children: ReactNode }) {
  const state = useAppState()
  const navigate = useNavigate()
  return state.activeProjectId ? <>{children}</> : <Empty title="Choose a project" detail="Select a project to view its saved results." action={<Button onClick={() => navigate('/projects')}>View projects</Button>} />
}

function RegenerateStage4Action({ projectId }: { projectId: string }) {
  const state = useAppState()
  const [confirming, setConfirming] = useState(false)
  const [regenerating, setRegenerating] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState(false)

  const regenerate = async () => {
    setRegenerating(true)
    setError('')
    try {
      await api.regenerateFromStage4(projectId)
      await Promise.all([state.refreshProjects(), state.refreshProjectArtifacts(projectId)])
      setConfirming(false)
      setSuccess(true)
      window.setTimeout(() => setSuccess(false), 4000)
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : 'Pipeline regeneration failed.')
    } finally {
      setRegenerating(false)
    }
  }

  return <>
    <Button variant="secondary" onClick={() => { setError(''); setConfirming(true) }} disabled={regenerating}>
      <RefreshCw className={regenerating ? 'spin' : ''} size={16} /> {regenerating ? 'Regenerating unit tests...' : 'Regenerate Unit Tests'}
    </Button>
    {confirming && <div className="dialog-backdrop" role="presentation"><div className="confirm-dialog regeneration-dialog" role="alertdialog" aria-modal="true" aria-labelledby="regenerate-title">
      <button className="dialog-close" aria-label="Close" onClick={() => setConfirming(false)} disabled={regenerating}><X size={18} /></button>
      <span className="dialog-regenerate"><RefreshCw size={21} /></span>
      <h2 id="regenerate-title">Regenerate Unit Tests</h2>
      <p>This keeps the existing repository analysis and refreshes:</p>
      <ul><li>Unit Test Generation</li><li>AI Verification</li><li>Quality Evaluation</li><li>Quality Optimization</li><li>Runtime Validation Plan</li></ul>
      {error && <ErrorNotice message={error} />}
      <div className="dialog-actions"><Button variant="secondary" onClick={() => setConfirming(false)} disabled={regenerating}>Cancel</Button><Button onClick={() => void regenerate()} disabled={regenerating}>{regenerating ? <><RefreshCw className="spin" size={16} /> Regenerating unit tests...</> : 'Regenerate Unit Tests'}</Button></div>
    </div></div>}
    {success && <div className="toast toast-success" role="status"><CheckCircle2 size={18} /> Unit tests regenerated successfully.</div>}
  </>
}

export function Dashboard() {
  const state = useAppState()
  const navigate = useNavigate()
  return <div className="landing-page">
    <div className="landing-content">
      <div className="eyebrow"><ShieldCheck size={16} /> TestForge · AI Unit Test Generator</div>
      <h1>Generate Production-Ready Unit Tests with AI</h1>
      <p>Upload your backend project, automatically analyze the source code, generate comprehensive unit tests, validate them against a running application, and export a production-ready test suite.</p>
      <div className="landing-actions">
        <button className="source-action" onClick={() => state.openUpload('zip')}><span><Upload size={24} /></span><div><strong>Generate Unit Tests</strong><small>Upload a backend project archive</small></div><ArrowRight size={20} /></button>
        <button className="source-action" onClick={() => state.openUpload('github')}><span><GitBranch size={24} /></span><div><strong>Import Project</strong><small>Import a public GitHub repository</small></div><ArrowRight size={20} /></button>
      </div>
      <div className="landing-assurance"><CheckCircle2 size={16} /><span>Production-ready pytest</span><CheckCircle2 size={16} /><span>Automatic AI verification</span><CheckCircle2 size={16} /><span>Runtime-validated results</span></div>
      {state.projects.length > 0 && <div className="recent-projects"><div className="recent-heading"><span>Recent projects</span><small>Select a project to review its repository overview</small></div><div className="recent-project-grid">{state.projects.slice(0, 3).map((project) => <button key={project.id} onClick={() => { state.setActiveProjectId(project.id); navigate(`/projects/${project.id}`) }}><span className="recent-project-icon">{project.source_type === 'GITHUB' ? <GitBranch size={18} /> : <FileArchive size={18} />}</span><div><strong>{project.name}</strong><small>{new Date(project.updated_at).toLocaleDateString()}</small></div><Badge tone={tone(project.status)}>{project.status}</Badge></button>)}</div></div>}
      <section className="dashboard-glance" aria-label="Product overview"><div><span>Projects</span><strong>{state.projects.length}</strong><small>Available repositories</small></div><div><span>Recent runs</span><strong>{Object.keys(state.jobs).length}</strong><small>Saved AI workspaces</small></div><div><span>Ready to generate</span><strong>{state.projects.filter((project) => project.status !== 'FAILED').length}</strong><small>Projects available</small></div></section>
    </div>
  </div>
}

export function Projects() {
  const state = useAppState()
  const navigate = useNavigate()
  const [query, setQuery] = useState('')
  const [pendingDelete, setPendingDelete] = useState<string | null>(null)
  const [deleting, setDeleting] = useState(false)
  const [deleteError, setDeleteError] = useState('')
  const filtered = state.projects.filter((project) => project.name.toLowerCase().includes(query.toLowerCase()))
  const selectProject = (id: string) => { state.setActiveProjectId(id); navigate(`/projects/${id}`) }
  const projectToDelete = state.projects.find((project) => project.id === pendingDelete)
  const confirmDelete = async () => {
    if (!pendingDelete) return
    setDeleting(true); setDeleteError('')
    try {
      await api.deleteProject(pendingDelete)
      state.removeProject(pendingDelete)
      setPendingDelete(null)
      await state.refreshProjects()
    } catch (reason) {
      setDeleteError(reason instanceof Error ? reason.message : 'The project could not be deleted.')
    } finally { setDeleting(false) }
  }
  return <div className="page"><PageHeader title="Projects" subtitle="Browse previous projects and reopen their saved test results." action={<div className="header-actions"><Button variant="secondary" onClick={() => state.openUpload('github')}><GitBranch size={16} /> Import GitHub</Button><Button onClick={() => state.openUpload('zip')}><Upload size={16} /> Upload ZIP</Button></div>} />
    <div className="project-toolbar"><div className="search-field"><Search size={17} /><input aria-label="Search projects" value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Search projects" /></div><span>{filtered.length} project{filtered.length === 1 ? '' : 's'}</span></div>
    {filtered.length ? <div className="project-card-grid">{filtered.map((project) => <article className="project-card" key={project.id}><button className="project-card-open" onClick={() => selectProject(project.id)}><div className="project-card-head"><span>{project.source_type === 'GITHUB' ? <GitBranch size={20} /> : <FileArchive size={20} />}</span><Badge tone={tone(project.status)}>{project.status}</Badge></div><h2>{project.name}</h2><p>{project.description || 'No project description provided.'}</p><div className="project-card-meta"><span>{project.source_type === 'GITHUB' ? 'GitHub repository' : 'ZIP archive'}</span><time>{new Date(project.updated_at).toLocaleDateString()}</time></div><div className="project-card-link">Open workspace <ArrowRight size={16} /></div></button><button className="project-delete" aria-label={`Delete ${project.name}`} onClick={() => { setPendingDelete(project.id); setDeleteError('') }}><Trash2 size={16} /> Delete</button></article>)}</div> : <Empty title="No projects found" detail={query ? 'Try a different search.' : 'Upload a ZIP or import a GitHub repository to get started.'} />}
    {projectToDelete && <div className="dialog-backdrop" role="presentation"><div className="confirm-dialog" role="alertdialog" aria-modal="true" aria-labelledby="delete-title"><button className="dialog-close" aria-label="Close" onClick={() => setPendingDelete(null)}><X size={18} /></button><span className="dialog-danger"><Trash2 size={21} /></span><h2 id="delete-title">Delete {projectToDelete.name}?</h2><p>This permanently removes the project and its saved analysis. This action cannot be undone.</p>{deleteError && <ErrorNotice message={deleteError} />}<div className="dialog-actions"><Button variant="secondary" onClick={() => setPendingDelete(null)} disabled={deleting}>Cancel</Button><Button onClick={confirmDelete} disabled={deleting}>{deleting ? 'Deleting…' : 'Delete project'}</Button></div></div></div>}
  </div>
}

export function ProjectRedirect() {
  const { id = '' } = useParams()
  const state = useAppState()
  useEffect(() => { if (id) state.setActiveProjectId(id) }, [id])
  const project = state.projects.find((item) => item.id === id)
  if (!project) return <div className="page"><PageHeader title="Project Overview" subtitle="Loading the selected repository." /><Loading /></div>
  return <div className="page project-overview-page"><ProjectOverview project={project} /></div>
}

export function ProcessingPage() {
  const { id = '' } = useParams()
  const state = useAppState()
  const navigate = useNavigate()
  const job = state.jobs[id]
  const [stage3Open, setStage3Open] = useState(true)
  const [jsonOpen, setJsonOpen] = useState(false)
  const [copied, setCopied] = useState(false)
  const currentStageNumber = Number(job?.currentStage?.slice(-1) ?? 1)
  const [reviewStage, setReviewStage] = useState(currentStageNumber)
  const [runtimeReport, setRuntimeReport] = useState<RuntimeValidationReport | null>(null)
  const [stageTab, setStageTab] = useState<'overview' | 'results' | 'logs' | 'raw'>('overview')
  const [clock, setClock] = useState(0)
  const [showActivityHistory, setShowActivityHistory] = useState(false)
  const [workspaceTab, setWorkspaceTab] = useState<'activity' | 'logs' | 'repository' | 'security' | 'generated'>('activity')
  const activityFeedRef = useRef<HTMLDivElement>(null)
  const agentActivityFeedRef = useRef<HTMLDivElement>(null)
  const understanding = state.artifacts.understanding
  const stage3 = understanding?.result
  const project = state.projects.find((item) => item.id === id)
  const securityScan = state.artifacts.securityScan
  const dependency = state.artifacts.dependency
  const projectMetadata = project?.ingestion_metadata ?? undefined
  const dependencyAnalysis = dependency?.analysis ?? {}
  const dependencyFiles = dependency?.files ?? []
  const entryPoints = dependencyFiles.filter((file) => file.is_entry_point).map((file) => file.path)
  const configurationFiles = dependencyFiles.filter((file) => /(^|\/)(pyproject\.toml|requirements[^/]*\.txt|setup\.(py|cfg)|package\.json|tsconfig[^/]*\.json|[^/]+\.(ya?ml|ini|cfg|toml|json))$/i.test(file.path)).map((file) => file.path)
  const dependencyGroups = (dependencyAnalysis.dependency_groups ?? {}) as Record<string, string[]>
  const stage3Functions = (stage3?.functions ?? []) as Array<Record<string, unknown>>
  const stage3Targets = (stage3?.test_targets ?? []) as Array<Record<string, unknown>>
  const productionFunctions = stage3Functions.filter((item) => !isRepositoryTestFile(item.file))
  const productionTargets = stage3Targets.filter((item) => !isRepositoryTestFile(item.file))
  const ignoredTestFiles = [...new Set([
    ...stage3Functions.filter((item) => isRepositoryTestFile(item.file)).map((item) => projectRelativePath(item.file)),
    ...stage3Targets.filter((item) => isRepositoryTestFile(item.file)).map((item) => projectRelativePath(item.file)),
  ])].sort()
  const uniqueImports = [...new Set((stage3?.imports ?? []).map((item) => String(item.module ?? '').trim()).filter(Boolean))].sort()
  const repositoryBehavior = (stage3?.repository_behavior ?? {}) as Record<string, unknown>
  const behaviorSideEffects = (repositoryBehavior.side_effects ?? {}) as Record<string, unknown>
  const behaviorExceptions = (repositoryBehavior.exceptions ?? {}) as Record<string, unknown>
  const callGraph = (stage3?.call_graph ?? []) as Array<Record<string, unknown>>
  const endpointRecords = (stage3?.api_endpoints ?? []) as unknown as Array<Record<string, unknown>>
  const classRecords = (stage3?.classes ?? []) as Array<Record<string, unknown>>
  const requestModels = (stage3?.api_endpoints ?? []).filter((item) => item.request_model ?? item.request_type)
  const responseModels = (stage3?.api_endpoints ?? []).filter((item) => item.response_model ?? item.response_type)
  const exceptionValues = [...new Set(productionFunctions.flatMap((item) => flattenExceptions(item.exceptions)))]
  const targetKeys = new Set(productionTargets.map((target) => `${projectRelativePath(target.file)}:${String(target.symbol ?? target.name ?? '')}`))
  const eligibleFunctions = productionFunctions.filter((item) => targetKeys.has(`${projectRelativePath(item.file)}:${String(item.name ?? item.symbol ?? '')}`))
  const excludedFunctions = productionFunctions.filter((item) => !eligibleFunctions.includes(item)).map((item) => {
    const name = String(item.name ?? item.symbol ?? 'Unknown function')
    const decorators = Array.isArray(item.decorators) ? item.decorators.map(String) : []
    const reason = name === '__init__' ? 'constructor' : name.startsWith('_') ? 'private helper' : decorators.some((value) => /validator/i.test(value)) ? 'validator function' : decorators.some((value) => /property/i.test(value)) ? 'property' : 'not selected as an executable runtime target'
    return { name, file: projectRelativePath(item.file), reason }
  })
  const behaviorRows = productionFunctions.map((item) => {
    const name = String(item.qualified_name ?? item.name ?? 'Unknown function')
    const shortName = String(item.name ?? name)
    const relatedEdges = callGraph.filter((edge) => [name, shortName].includes(String(edge.caller ?? '')))
    const endpoint = endpointRecords.find((candidate) => [name, shortName].includes(String(candidate.handler ?? '')))
    return {
      name,
      file: projectRelativePath(item.file),
      calls: stringValues(item.calls).length ? stringValues(item.calls) : relatedEdges.map((edge) => String(edge.callee ?? '')).filter(Boolean),
      returns: item.return_type == null ? [] : [String(item.return_type)],
      exceptions: flattenExceptions(item.exceptions).length
        ? flattenExceptions(item.exceptions)
        : flattenExceptions(behaviorExceptions[name] ?? behaviorExceptions[shortName]),
      dependencies: stringValues(endpoint?.dependencies),
      sideEffects: stringValues(item.side_effects).length
        ? stringValues(item.side_effects)
        : stringValues(behaviorSideEffects[name] ?? behaviorSideEffects[shortName]),
    }
  }).filter((item) => item.calls.length || item.returns.length || item.exceptions.length || item.dependencies.length || item.sideEffects.length)
  const stage3Groups = stage3 ? [
    ['Modules', stage3.modules ?? []],
    ['Imports', uniqueImports.map((module) => ({ module }))],
    ['Functions', productionFunctions],
    ['Classes', stage3.classes ?? []],
    ['Endpoints', stage3.api_endpoints ?? []],
    ['Request Models', requestModels],
    ['Response Models', responseModels],
    ['SQLAlchemy Models', (stage3.classes ?? stage3.data_models ?? []).filter((item) => Array.isArray(item.sqlalchemy_model_usage) && item.sqlalchemy_model_usage.length > 0)],
    ['Exceptions', exceptionValues.map((name) => ({ name }))],
    ['Test Targets', productionTargets],
    ['Semgrep Findings', stage3.security_findings ?? []],
  ] as const : []
  const rawStage3Json = understanding ? JSON.stringify(understanding, null, 2) : ''
  const stage4Generation = state.artifacts.generation
  const stage4Tests = stage4Generation?.generated_test_cases ?? []
  const stage4Categories = stage4Tests.reduce<Record<string, number>>((counts, test) => ({ ...counts, [test.category]: (counts[test.category] ?? 0) + 1 }), {})
  const generatedPytest = stage4Tests.map((test) => test.unit_test?.generated_code).filter((code): code is string => Boolean(code)).join('\n\n')
  const stage4Duration = job?.logs?.find((line) => line.startsWith('Stage 4 generation duration:'))?.split(':').slice(1).join(':').trim() ?? unavailable
  const coverageTargets = (productionTargets.length ? productionTargets : productionFunctions).reduce<Array<{ file: string; symbol: string }>>((items, target) => {
    const candidate = { file: projectRelativePath(target.file), symbol: symbolName(target.symbol ?? target.name ?? target.qualified_name) }
    return candidate.symbol && !items.some((item) => item.file === candidate.file && item.symbol === candidate.symbol) ? [...items, candidate] : items
  }, [])
  const coveredTargets = coverageTargets.filter((target) => stage4Tests.some((test) => {
    const testFile = projectRelativePath(test.unit_test?.file ?? test.traceability?.file ?? test.traceability?.source_file ?? test.traceability?.target_file)
    const testSymbol = symbolName(test.unit_test?.symbol ?? test.traceability?.symbol ?? test.traceability?.target ?? test.traceability?.target_symbol)
    return target.symbol === testSymbol && (testFile === unavailable || target.file === testFile || target.file.endsWith(`/${testFile}`) || testFile.endsWith(`/${target.file}`))
  }))
  const stage4Coverage = coverageTargets.length ? Math.min(100, Math.round((coveredTargets.length / coverageTargets.length) * 10000) / 100) : 0
  const duplicateTestsRemoved = Math.max(0, (stage4Generation?.total_generated ?? 0) - (stage4Generation?.total_after_deduplication ?? 0))
  const categoryTotal = (pattern: RegExp) => Object.entries(stage4Categories).filter(([name]) => pattern.test(name)).reduce((total, [, count]) => total + count, 0)
  const uniqueCategoryTargets = (pattern: RegExp) => new Set(stage4Tests.filter((test) => pattern.test(test.category)).map((test) => symbolName(test.unit_test?.symbol ?? test.traceability?.symbol ?? test.traceability?.target ?? test.traceability?.target_symbol)).filter(Boolean)).size
  const stage5Verification = state.artifacts.verification
  const verificationResults = stage5Verification?.results ?? []
  const verificationByTest = new Map(verificationResults.map((result) => [result.test_case_id, result]))
  const verificationTotal = verificationResults.length
  const verificationCoverage = verificationTotal ? Math.round(((stage5Verification?.summary.verified ?? 0) / verificationTotal) * 10000) / 100 : 0
  const averageConfidence = verificationTotal ? Math.round((verificationResults.reduce((total, result) => total + (result.confidence <= 1 ? result.confidence * 100 : result.confidence), 0) / verificationTotal) * 100) / 100 : 0
  const verificationDuration = job?.logs?.find((line) => line.startsWith('Verification duration:'))?.split(':').slice(1).join(':').trim() ?? unavailable
  const metricPercent = (passed: number, total: number) => total ? Math.round((passed / total) * 10000) / 100 : 100
  const tracedResults = verificationResults.filter((result) => result.evidence.length > 0).length
  const behaviorChecks = verificationResults.flatMap((result) => result.findings).filter((finding) => /behavior|return|exception|side.effect/i.test(finding.check))
  const exceptionTests = stage4Tests.filter((test) => /exception/i.test(test.category))
  const securityTests = stage4Tests.filter((test) => /security/i.test(test.category))
  const boundaryTests = stage4Tests.filter((test) => /boundary/i.test(test.category))
  const verifiedCategoryCount = (tests: typeof stage4Tests) => tests.filter((test) => verificationByTest.get(test.id)?.status === 'Verified').length
  const maintainableTests = stage4Tests.filter((test) => /\bassert\b/.test(test.unit_test?.generated_code ?? '')).length
  const semanticCorrectness = verificationTotal ? Math.round((((stage5Verification?.summary.verified ?? 0) + ((stage5Verification?.summary.partial ?? 0) * 0.5)) / verificationTotal) * 10000) / 100 : 0
  const duplicateVerificationCount = verificationResults.filter((result) => result.findings.some((finding) => finding.check === 'duplicate' && finding.status !== 'Verified')).length
  const securityStatusCounts = securityTests.reduce((counts, test) => { const status = verificationByTest.get(test.id)?.status ?? 'Failed'; return { ...counts, [status]: (counts[status] ?? 0) + 1 } }, {} as Record<string, number>)
  const securitySemanticCoverage = securityTests.length ? Math.round((((securityStatusCounts.Verified ?? 0) + ((securityStatusCounts.Partial ?? 0) * 0.5)) / securityTests.length) * 10000) / 100 : 100
  const groupedVerificationFindings = verificationResults.flatMap((result) => result.findings.filter((finding) => finding.status !== 'Verified').map((finding) => ({ ...finding, testId: result.test_case_id }))).reduce<Array<{ check: string; detail: string; status: 'Partial' | 'Failed'; testIds: string[] }>>((groups, finding) => { const existing = groups.find((group) => group.check === finding.check && group.detail === finding.detail); if (existing) { existing.testIds.push(finding.testId); return groups } return [...groups, { check: finding.check, detail: finding.detail, status: finding.status as 'Partial' | 'Failed', testIds: [finding.testId] }] }, [])
  const finalRecommendation = (stage5Verification?.summary.failed ?? 0) > 0 ? 'REGENERATE TESTS' : (stage5Verification?.summary.partial ?? 0) > 0 ? 'REVIEW REQUIRED' : 'READY FOR QUALITY OPTIMIZATION'
  const quality = state.artifacts.quality
  const stageNames = ['Project Setup', 'Repository & Security Analysis', 'Test Target Analysis', 'Unit Test Generation', 'AI Verification', 'Quality Optimization', 'Runtime Validation']
  const stagePercentages = [15, 30, 45, 60, 80, 92, 100]
  const stageStatus = (stage: number) => stage < currentStageNumber ? 'completed' : stage > currentStageNumber ? 'pending' : job?.status === 'failed' ? 'failed' : job?.status === 'paused' ? 'waiting' : job?.status === 'complete' ? 'completed' : 'running'
  const stageMetric = (stage: number) => [
    metadataValue(projectMetadata, 'total_files', 'file_count') == null ? 'Extracting project…' : `${displayArtifact(metadataValue(projectMetadata, 'total_files', 'file_count'))} files`,
    securityScan && dependency ? `${securityScan.summary?.total_findings ?? 0} security findings` : 'Discovering dependencies and scanning…',
    stage3 ? `${productionFunctions.length} functions · ${endpointRecords.length} endpoints` : 'Analyzing repository behavior…',
    stage4Generation ? `${stage4Generation.total_after_deduplication} generated tests` : 'Generating unit tests…',
    stage5Verification ? `${stage5Verification.summary.verified} verified · ${stage5Verification.summary.failed} failed` : 'Verifying generated tests…',
    quality ? `${quality.final_score}% quality · ${quality.optimized_test_suite.length} tests` : 'Quality pending',
    runtimeReport ? `${runtimeReport.pass_rate}% pass rate · ${runtimeReport.summary.failed} failed` : 'Executing runtime validation…',
  ][stage - 1] + ` · ${stagePercentages[stage - 1]}% milestone`
  const rawStageArtifact = [project, { dependency, security_scan: securityScan }, understanding, stage4Generation, stage5Verification, quality, runtimeReport][reviewStage - 1]
  const stageDataReady = [Boolean(project), Boolean(dependency || securityScan), Boolean(stage3), Boolean(stage4Generation), Boolean(stage5Verification), Boolean(quality), Boolean(runtimeReport)][reviewStage - 1]
  const elapsedMs = clock ? Math.max(0, clock - (job?.timeline[0]?.at.getTime() ?? clock)) : 0
  const elapsed = `${Math.floor(elapsedMs / 60000)}m ${Math.floor((elapsedMs % 60000) / 1000)}s`
  const visibleActivity = showActivityHistory ? job?.timeline ?? [] : (job?.timeline ?? []).slice(-100)
  const hiddenActivityCount = Math.max(0, (job?.timeline.length ?? 0) - 100)
  const workspaceFile = projectRelativePath(dependencyFiles.at(-1)?.path)
  const workspaceTargetRecord = productionTargets.at(-1)
  const workspaceTarget = String(workspaceTargetRecord?.symbol ?? workspaceTargetRecord?.name ?? '')
  const workspaceClass = String(workspaceTargetRecord?.class_name ?? workspaceTargetRecord?.class ?? '')
  const workspaceFunction = symbolName(workspaceTargetRecord?.symbol ?? workspaceTargetRecord?.name)
  const executionSeconds = Math.max(0, Math.floor(elapsedMs / 1000))
  const executionSpeed = executionSeconds > 0 && stage4Tests.length ? `${(stage4Tests.length / executionSeconds).toFixed(2)} tests/sec` : 'Measuring…'
  const generationTimestamp = [...(job?.timeline ?? [])].reverse().find((event) => /generated|generation complete/i.test(`${event.label} ${event.detail}`))?.at ?? null
  const copyStage3 = async () => {
    if (!understanding) return
    await navigator.clipboard.writeText(rawStage3Json)
    setCopied(true)
    window.setTimeout(() => setCopied(false), 1500)
  }
  useEffect(() => { if (id && state.activeProjectId !== id) state.setActiveProjectId(id) }, [id])
  useEffect(() => { setReviewStage(currentStageNumber); setStageTab('overview') }, [currentStageNumber])
  useEffect(() => {
    if (job?.status !== 'running') return
    const timer = window.setInterval(() => setClock(Date.now()), 1000)
    return () => window.clearInterval(timer)
  }, [job?.status])
  useEffect(() => {
    if (job?.status === 'running') {
      activityFeedRef.current?.scrollTo({ top: activityFeedRef.current.scrollHeight, behavior: 'smooth' })
      agentActivityFeedRef.current?.scrollTo({ top: agentActivityFeedRef.current.scrollHeight, behavior: 'smooth' })
    }
  }, [job?.timeline.length, job?.status])
  useEffect(() => {
    if (currentStageNumber < 7) return
    const runId = sessionStorage.getItem(`testforge-runtime-run:${id}`)
    if (runId) void api.runtimeValidationReport(runId).then(setRuntimeReport).catch(() => undefined)
  }, [currentStageNumber, id, job?.status])
  useEffect(() => {
    if (!stage4Generation || job?.status === 'failed') return
    navigate(`/ai-test-results/${id}`, { replace: true })
  }, [id, job?.status, navigate, stage4Generation])
  if (!job) return <div className="page narrow"><PageHeader title="Loading saved results" subtitle="Checking the latest analysis for this project." /><Loading /></div>
  const securityCheckpoint = state.workflowMode(id) === 'quick'
    && job.status === 'paused'
    && job.currentStage === 'stage_2'
    && securityScan?.status === 'completed'
    && !understanding
  if (securityCheckpoint && project && securityScan) return <SecurityReview project={project} scan={securityScan} dependency={dependency} onContinue={() => state.continueAfterSecurity(project)} />
  const resumeAutomaticProcessing = () => {
    if (!project) return
    if (['stage_4', 'stage_5', 'stage_6'].includes(job.currentStage ?? '')) state.continuePipeline(project)
    else state.approveNextStage(project)
  }
  return <div className="assistant-page processing-redesign"><div className="assistant-workspace">
    <header className={`live-run-header ${job.status}`}><div><span className="run-kicker">TestForge · AI Unit Test Generator · {job.projectName}</span><h1>{job.status === 'running' ? 'Running' : job.status === 'paused' ? 'Review' : job.status === 'failed' ? 'Attention needed' : 'Completed'} — {stageNames[currentStageNumber - 1]}</h1><p>{job.stage} · {state.workflowMode(id) === 'quick' ? 'Quick Mode' : 'Review Mode'}</p></div><div className="run-header-metrics"><span>Progress<strong>{job.progress}%</strong></span><span>Elapsed<strong>{elapsed}</strong></span><span>Remaining<strong>{job.estimatedTime}</strong></span><Badge tone={job.status === 'failed' ? 'danger' : job.status === 'complete' ? 'success' : job.status === 'paused' ? 'warning' : 'info'}>{job.status === 'paused' ? 'Waiting' : job.status}</Badge></div><div className="progress-track"><i style={{ width: `${job.progress}%` }} /></div></header>
    {job.status === 'failed' && job.error && <ErrorNotice message={job.error} />}
    {job.resumedStage && <p className="muted">Resumed stage: {job.resumedStage.replaceAll('_', ' ')}</p>}
    <GenerateWorkspace job={job} project={project} dependency={dependency} understanding={understanding} security={securityScan} generation={stage4Generation} verification={stage5Verification} runtime={runtimeReport} coverage={stage4Generation ? stage4Coverage : null} elapsed={elapsed} onResume={resumeAutomaticProcessing} onRuntime={() => navigate(`/runtime-validation/${id}`)} onExport={() => downloadTestSuite(id)} />
    <section className="agent-workspace" aria-label="Generate Tests AI workspace">
      <header className="agent-workspace-header">
        <div className="agent-project"><span className="agent-avatar"><Sparkles size={18} /></span><div><small>AI unit test workspace</small><h2>{job.projectName}</h2><p>{project?.source_type === 'GITHUB' ? 'GitHub repository' : 'Uploaded repository'}{project?.description ? ` · ${project.description}` : ''}</p></div></div>
        <div className="agent-progress"><span><strong>{job.progress}%</strong> complete</span><div className="progress-track"><i style={{ width: `${job.progress}%` }} /></div><small>{job.estimatedTime === unavailable ? 'Estimating remaining time…' : `${job.estimatedTime} remaining`}</small></div>
        <Badge tone={job.status === 'failed' ? 'danger' : job.status === 'complete' ? 'success' : job.status === 'paused' ? 'warning' : 'info'}>{job.status === 'paused' ? 'Review required' : job.status}</Badge>
      </header>

      {job.status === 'complete' && <div className="agent-complete"><div><CheckCircle2 size={22} /><span><strong>Unit Test Generation Complete</strong><small>Your generated suite is ready to export or validate.</small></span></div><div><RegenerateStage4Action projectId={id} /><Button variant="secondary" onClick={() => navigate(`/runtime-validation/${id}`)}>Open Runtime Validation</Button><Button variant="secondary" disabled={!generatedPytest} onClick={() => downloadText(`${job.projectName}-generated-tests`, generatedPytest)}>Export Test Suite</Button><Button onClick={() => navigate('/reports')}>View Report</Button></div></div>}

      <div className="agent-workspace-body">
        <main className="agent-focus">
          <div className="agent-task-heading"><div><span className={job.status === 'running' ? 'agent-pulse' : ''}><BrainCircuit size={19} /></span><div><small>AI Agent · Current task</small><h3>{stageNames[currentStageNumber - 1]}</h3><p>{job.stage}</p></div></div><strong>{stage4Generation?.total_after_deduplication ?? 0}<small> tests generated</small></strong></div>
          <div className="agent-context-grid">
            <div><small>Current file</small><strong>{workspaceFile === unavailable ? 'Indexing repository…' : workspaceFile}</strong></div>
            <div><small>Current class</small><strong>{workspaceClass || (stage3 ? 'No class context' : 'Discovering classes…')}</strong></div>
            <div><small>Current function</small><strong>{workspaceFunction || (stage3 ? 'No function context' : 'Discovering functions…')}</strong></div>
            <div><small>Current operation</small><strong>{job.status === 'paused' ? 'Waiting for review' : job.stage}</strong></div>
          </div>

          <nav className="agent-tabs" aria-label="Workspace views">{([
            ['activity', 'Activity'], ['logs', 'Terminal Logs'], ['repository', 'Repository Analysis'], ['security', 'Security Analysis'], ['generated', 'Generated Tests'],
          ] as const).map(([key, label]) => <button key={key} className={workspaceTab === key ? 'active' : ''} onClick={() => setWorkspaceTab(key)}>{label}{key === 'generated' && stage4Tests.length > 0 && <span>{stage4Tests.length}</span>}</button>)}</nav>

          {workspaceTab === 'generated' && <TestExplorer tests={stage4Tests} verification={stage5Verification ?? null} runtime={runtimeReport} coverage={stage4Generation ? stage4Coverage : null} generationStatus={stage4Generation?.generation_status} generationTimestamp={generationTimestamp} projectName={job.projectName} projectId={id} onOpenRuntime={() => navigate(`/runtime-validation/${id}`)} />}
          <div className={`agent-panel ${workspaceTab === 'generated' ? 'test-explorer-active' : ''}`}>
            {workspaceTab === 'activity' && <div className="agent-feed" ref={agentActivityFeedRef}>{visibleActivity.length ? visibleActivity.map((activity) => <article key={activity.id} className={activity.status}><time>{activity.at.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })}</time><span>{activity.status === 'failed' ? <CircleAlert size={15} /> : activity.status === 'active' ? <Sparkles size={15} /> : <CheckCircle2 size={15} />}</span><div><strong>{activity.label}</strong><p>{activity.detail}</p></div></article>) : <div className="agent-placeholder"><Sparkles size={20} /><strong>Preparing AI activity…</strong><span>Events will appear as repository analysis begins.</span></div>}</div>}
            {workspaceTab === 'logs' && <div className="agent-terminal"><header><i /><i /><i /><span>testforge-agent</span></header><pre>{job.logs?.length ? job.logs.join('\n') : 'Waiting for execution output…'}</pre></div>}
            {workspaceTab === 'repository' && <div className="agent-analysis"><div className="agent-analysis-summary"><div><strong>{dependencyFiles.length || 'Indexing…'}</strong><span>Files analyzed</span></div><div><strong>{stage3 ? productionFunctions.length : 'Analyzing…'}</strong><span>Functions</span></div><div><strong>{stage3 ? classRecords.length : 'Analyzing…'}</strong><span>Classes</span></div><div><strong>{stage3 ? productionTargets.length : 'Analyzing…'}</strong><span>Test targets</span></div></div>{understanding ? <details><summary>View repository analysis details</summary><pre>{JSON.stringify(understanding, null, 2)}</pre></details> : <div className="agent-placeholder"><BrainCircuit size={20} /><strong>Analyzing repository structure…</strong><span>Functions, classes, and test targets will appear here.</span></div>}</div>}
            {workspaceTab === 'security' && <div className="agent-security">{securityScan ? <><div className="agent-analysis-summary"><div><strong>{securityScan.summary?.files_scanned ?? 'Scanning…'}</strong><span>Files scanned</span></div><div><strong>{securityScan.summary?.total_findings ?? 'Scanning…'}</strong><span>Findings</span></div><div><strong>{securityScan.summary?.by_severity?.CRITICAL ?? 0}</strong><span>Critical</span></div><div><strong>{securityScan.summary?.by_severity?.HIGH ?? securityScan.summary?.by_severity?.ERROR ?? 0}</strong><span>High</span></div></div><div className="agent-findings">{securityScan.findings.map((finding) => <details key={finding.id}><summary><Badge tone={/CRITICAL|HIGH|ERROR/.test(finding.severity) ? 'danger' : 'warning'}>{finding.severity}</Badge><strong>{readableRuleName(finding.rule_id)}</strong><small>{projectRelativePath(finding.file)}:{finding.line}</small></summary><p>{finding.message}</p>{finding.recommendation && <small>{finding.recommendation}</small>}</details>)}</div></> : <div className="agent-placeholder"><ShieldCheck size={20} /><strong>Scanning for security risks…</strong><span>Security findings will appear when analysis is available.</span></div>}</div>}
            {workspaceTab === 'generated' && <div className="generated-workspace">{generatedPytest ? <><div className="code-preview-toolbar"><div><Code2 size={16} /><strong>generated_tests.py</strong></div><div><Button variant="secondary" onClick={async () => { await navigator.clipboard.writeText(generatedPytest); setCopied(true); window.setTimeout(() => setCopied(false), 1500) }}><Clipboard size={15} /> {copied ? 'Copied' : 'Copy'}</Button><Button variant="secondary" onClick={() => downloadText(`${job.projectName}-generated-tests`, generatedPytest)}><Download size={15} /> Download</Button></div></div><pre className="code-preview"><code>{generatedPytest}</code></pre><details className="generated-test-index"><summary>Expand generated test index ({stage4Tests.length})</summary><div>{stage4Tests.map((test) => <article key={test.id}><strong>{test.title}</strong><span>{test.category}</span><small>{symbolName(test.unit_test?.symbol ?? test.traceability?.symbol ?? test.traceability?.target)}</small></article>)}</div></details></> : <div className="agent-placeholder"><Code2 size={20} /><strong>Generating production-ready tests…</strong><span>The code preview will appear as soon as generated test data is available.</span></div>}</div>}
          </div>
        </main>

        <aside className="agent-summary" aria-label="Workspace summary"><header><Gauge size={17} /><strong>Workspace summary</strong></header><dl><div><dt>Files analyzed</dt><dd>{dependencyFiles.length || 'Indexing…'}</dd></div><div><dt>Functions discovered</dt><dd>{stage3 ? productionFunctions.length : 'Analyzing…'}</dd></div><div><dt>Classes discovered</dt><dd>{stage3 ? classRecords.length : 'Analyzing…'}</dd></div><div><dt>Generated tests</dt><dd>{stage4Generation?.total_after_deduplication ?? 'Generating…'}</dd></div><div><dt>Coverage estimate</dt><dd>{stage4Generation ? `${stage4Coverage}%` : 'Estimating…'}</dd></div><div><dt>Security findings</dt><dd>{securityScan?.summary?.total_findings ?? 'Scanning…'}</dd></div><div><dt>Execution speed</dt><dd>{executionSpeed}</dd></div><div><dt>Runtime readiness</dt><dd>{runtimeReport ? `${runtimeReport.pass_rate}% pass rate` : stage5Verification ? 'Ready to validate' : 'Preparing…'}</dd></div></dl></aside>
      </div>
    </section>
    <section className="ai-workspace" aria-label="AI unit test generation workspace"><header className="ai-workspace-head"><div><span>Current task</span><h2>{stageNames[currentStageNumber - 1]}</h2><p>{job.status === 'running' ? 'TestForge is actively working on your unit test suite.' : job.status === 'paused' ? 'Your review is required before TestForge continues.' : job.status === 'failed' ? 'TestForge stopped and needs your attention.' : 'Your production-ready unit test suite is ready.'}</p></div><Badge tone={job.status === 'failed' ? 'danger' : job.status === 'complete' ? 'success' : job.status === 'paused' ? 'warning' : 'info'}>{job.status === 'paused' ? 'Review required' : job.status}</Badge></header><div className="ai-workspace-live"><div><span>Current file</span><strong>{workspaceFile === unavailable ? 'Analyzing repository…' : workspaceFile}</strong></div><div><span>Current target</span><strong>{workspaceTarget || 'Identifying test targets…'}</strong></div><div><span>Current operation</span><strong>{job.stage}</strong></div><div><span>Generated tests</span><strong>{stage4Generation?.total_after_deduplication ?? (currentStageNumber < 4 ? 'Preparing…' : 'Generating…')}</strong></div></div>{stage4Generation && <details className="workspace-generated-tests" open={job.status === 'paused' && currentStageNumber === 4}><summary><span><strong>{stage4Generation.total_after_deduplication} generated unit tests</strong><small>Review the suite before AI verification</small></span><ChevronDown size={17} /></summary><div><div className="workspace-test-list">{stage4Tests.slice(0, 30).map((test) => <article key={test.id}><strong>{test.title}</strong><small>{test.id} · {symbolName(test.unit_test?.symbol ?? test.traceability?.symbol ?? test.traceability?.target)}</small><Badge tone={/security/i.test(test.category) ? 'warning' : 'info'}>{test.category}</Badge></article>)}</div><div className="stage3-actions"><Button variant="secondary" disabled={!generatedPytest} onClick={() => downloadText(`${job.projectName}-generated-tests`, generatedPytest)}><Download size={15} /> Export Pytest Suite</Button><Button variant="secondary" onClick={() => download(`${job.projectName}-unit-test-generation`, stage4Generation)}><Download size={15} /> Export Test Suite JSON</Button></div></div></details>}<nav className="workspace-tabs" aria-label="AI workspace views">{(['activity', 'logs', 'repository', 'security'] as const).map((tab) => <button key={tab} className={workspaceTab === tab ? 'active' : ''} onClick={() => setWorkspaceTab(tab)}>{tab === 'repository' ? 'Repository Analysis' : tab === 'security' ? 'Security Analysis' : tab.charAt(0).toUpperCase() + tab.slice(1)}</button>)}</nav><div className="workspace-tab-content">{workspaceTab === 'activity' && <div className="workspace-activity" ref={activityFeedRef}>{visibleActivity.map((activity, index) => <article key={activity.id} className={activity.status}><time>{activity.at.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</time><span>{activity.status === 'failed' ? <CircleAlert size={15} /> : activity.status === 'active' ? <Sparkles size={15} /> : <CheckCircle2 size={15} />}</span><div><strong>{activity.label}</strong><p>{activity.detail}</p></div>{index === visibleActivity.length - 1 && job.status === 'running' && <Badge tone="info">Live</Badge>}</article>)}{hiddenActivityCount > 0 && <Button variant="secondary" onClick={() => setShowActivityHistory((visible) => !visible)}>{showActivityHistory ? 'Show latest activity' : `Show ${hiddenActivityCount} earlier events`}</Button>}</div>}{workspaceTab === 'logs' && <div className="workspace-terminal"><header><i /><i /><i /><span>TestForge execution log</span></header><pre>{job.logs?.length ? job.logs.join('\n') : 'Waiting for execution output…'}</pre></div>}{workspaceTab === 'repository' && <div className="workspace-analysis"><div className="live-metric-grid"><div><span>Modules</span><strong>{stage3?.modules?.length ?? 'Analyzing…'}</strong></div><div><span>Functions</span><strong>{stage3 ? productionFunctions.length : 'Analyzing…'}</strong></div><div><span>Endpoints</span><strong>{stage3 ? endpointRecords.length : 'Analyzing…'}</strong></div><div><span>Models</span><strong>{stage3 ? classRecords.length : 'Analyzing…'}</strong></div><div><span>Test targets</span><strong>{stage3 ? productionTargets.length : 'Analyzing…'}</strong></div><div><span>Call graph</span><strong>{stage3?.call_graph ? 'Available' : 'Analyzing…'}</strong></div></div>{understanding && <details className="raw-debug-panel"><summary>Repository analysis details</summary><pre>{JSON.stringify(understanding, null, 2)}</pre></details>}</div>}{workspaceTab === 'security' && <div className="workspace-security"><div className="live-metric-grid"><div><span>Files scanned</span><strong>{securityScan?.summary?.files_scanned ?? 'Scanning…'}</strong></div><div><span>Findings</span><strong>{securityScan?.summary?.total_findings ?? 'Scanning…'}</strong></div><div><span>Critical</span><strong>{securityScan?.summary?.by_severity?.CRITICAL ?? 0}</strong></div><div><span>High</span><strong>{securityScan?.summary?.by_severity?.HIGH ?? securityScan?.summary?.by_severity?.ERROR ?? 0}</strong></div></div>{securityScan?.findings.length ? <div className="workspace-findings">{securityScan.findings.map((finding) => <details key={finding.id}><summary><Badge tone={finding.severity === 'ERROR' || finding.severity === 'HIGH' || finding.severity === 'CRITICAL' ? 'danger' : 'warning'}>{finding.severity}</Badge><strong>{readableRuleName(finding.rule_id)}</strong><small>{projectRelativePath(finding.file)}:{finding.line}</small></summary><p>{finding.message}</p><small>{displayArtifact(finding.recommendation)}</small></details>)}</div> : <p className="muted">{securityScan?.status === 'completed' ? 'No security findings affect this unit test suite.' : 'Security analysis is running…'}</p>}</div>}</div></section>
    <div className="processing-layout"><aside className="stage-timeline" aria-label="Pipeline stages">{stageNames.map((name, index) => { const number = index + 1; const status = stageStatus(number); return <button key={name} className={`${status} ${reviewStage === number ? 'selected' : ''}`} onClick={() => { setReviewStage(number); setStageTab('overview') }} disabled={number > currentStageNumber}><span className="stage-node">{status === 'completed' ? <CheckCircle2 size={17} /> : status === 'failed' ? <CircleAlert size={17} /> : status === 'running' ? <RefreshCw className="spin" size={17} /> : number}</span><span><small>Stage {number}</small><strong>{name}</strong><em>{status === 'waiting' ? 'Waiting for approval' : status}</em></span></button> })}</aside><main className="stage-focus"><nav className="stage-shortcuts"><Button variant="secondary" disabled={reviewStage <= 1} onClick={() => { setReviewStage((stage) => Math.max(1, stage - 1)); setStageTab('overview') }}>Previous Stage</Button><span>Reviewing Stage {reviewStage} of 7</span><Button variant="secondary" disabled={reviewStage >= currentStageNumber} onClick={() => { setReviewStage((stage) => Math.min(currentStageNumber, stage + 1)); setStageTab('overview') }}>Next Stage</Button></nav><details key={`${reviewStage}-${currentStageNumber}`} className="stage-review-card" open={reviewStage === currentStageNumber}><summary><span><small>Stage {reviewStage}</small><strong>{stageNames[reviewStage - 1]}</strong><em>{stageMetric(reviewStage)} · Duration: {reviewStage === 4 ? stage4Duration : unavailable}</em></span><Badge tone={stageStatus(reviewStage) === 'completed' ? 'success' : stageStatus(reviewStage) === 'failed' ? 'danger' : stageStatus(reviewStage) === 'waiting' ? 'warning' : 'info'}>{stageStatus(reviewStage)}</Badge><ChevronDown size={17} /></summary><nav className="stage-tabs" aria-label="Stage detail views">{(['overview', 'results', 'logs', 'raw'] as const).map((tab) => <button key={tab} className={stageTab === tab ? 'active' : ''} onClick={() => setStageTab(tab)}>{tab === 'raw' ? 'Raw JSON' : tab.charAt(0).toUpperCase() + tab.slice(1)}</button>)}</nav><div className="stage-review-content">
    {stageTab === 'overview' && <section className="stage-overview"><div className="live-metric-grid"><div><span>Status</span><strong>{stageStatus(reviewStage)}</strong></div><div><span>Key result</span><strong>{stageMetric(reviewStage)}</strong></div><div><span>Elapsed time</span><strong>{elapsed}</strong></div>{reviewStage === 2 && dependency && <><div><span>Dependencies</span><strong>{Number(dependencyAnalysis.dependency_count ?? Object.values(dependencyGroups).flat().length)}</strong></div><div><span>Files discovered</span><strong>{dependency.files.length}</strong></div><div><span>Security findings</span><strong>{securityScan?.summary?.total_findings ?? 0}</strong></div></>}{reviewStage === 3 && <><div><span>Modules</span><strong>{stage3?.modules?.length ?? 0}</strong></div><div><span>Functions</span><strong>{productionFunctions.length}</strong></div><div><span>Test targets</span><strong>{productionTargets.length}</strong></div></>}{reviewStage === 4 && <><div><span>Tests generated</span><strong>{stage4Generation?.total_after_deduplication ?? 0}</strong></div><div><span>Coverage</span><strong>{stage4Coverage}%</strong></div><div><span>Security tests</span><strong>{securityTests.length}</strong></div></>}</div><p className="stage-overview-hint">Open Results for complete stage output, Logs for execution details, or Raw JSON for debugging.</p></section>}
    {stageTab === 'overview' && job.status === 'running' && reviewStage === currentStageNumber && !stageDataReady && <section className="agent-working" aria-live="polite"><span className="agent-working-icon"><Sparkles size={18} /></span><div><strong>{stageMetric(reviewStage)}</strong><small>Live results will appear here as TestForge completes this operation.</small><i /><i /><i /></div></section>}
    {stageTab === 'overview' && reviewStage === 2 && securityScan && <section className="severity-dashboard">{['CRITICAL', 'HIGH', 'MEDIUM', 'LOW'].map((severity) => <div key={severity} className={severity.toLowerCase()}><span>{severity}</span><strong>{securityScan.summary?.by_severity?.[severity] ?? (severity === 'HIGH' ? securityScan.summary?.by_severity?.ERROR : severity === 'MEDIUM' ? securityScan.summary?.by_severity?.WARNING : severity === 'LOW' ? securityScan.summary?.by_severity?.INFO : 0) ?? 0}</strong></div>)}</section>}
    {stageTab === 'overview' && reviewStage === 5 && stage5Verification && <section className="verification-dashboard"><MetricCard icon={CheckCircle2} title="Verified" value={stage5Verification.summary.verified} helper="Semantically confirmed" /><MetricCard icon={CircleAlert} title="Partial" value={stage5Verification.summary.partial} helper="Review recommended" /><MetricCard icon={X} title="Failed" value={stage5Verification.summary.failed} helper="Requires correction" /><MetricCard icon={Gauge} title="Confidence" value={`${averageConfidence}%`} helper="Average confidence" /></section>}
    {stageTab === 'overview' && reviewStage === 6 && quality && <section className="quality-bars">{Object.entries(quality.quality_evaluation.dimension_scores).map(([dimension, score]) => <div key={dimension}><span>{dimension.replaceAll('_', ' ')}</span><strong>{score}%</strong><div><i style={{ width: `${Math.max(0, Math.min(100, score))}%` }} /></div></div>)}</section>}
    {stageTab === 'overview' && reviewStage === 7 && runtimeReport && <section className="verification-dashboard"><MetricCard icon={Gauge} title="Pass Rate" value={`${runtimeReport.pass_rate}%`} helper="Runtime success" /><MetricCard icon={CheckCircle2} title="Passed" value={runtimeReport.summary.passed} helper="Tests passed" /><MetricCard icon={CircleAlert} title="Failed" value={runtimeReport.summary.failed} helper="Tests failed" /><MetricCard icon={Clock3} title="Duration" value={`${runtimeReport.duration_ms} ms`} helper="Total execution" /></section>}
    {stageTab === 'results' && <>
    {reviewStage === 1 && project && <section className="stage-output-card validation-output"><h2>Project Setup</h2><dl>
      <ArtifactField label="Project Name" value={project.name} />
      <ArtifactField label="Project ID" value={project.id} />
      <ArtifactField label="Upload Source" value={project.source_type} />
      <ArtifactField label="Upload Time" value={project.created_at} />
      <ArtifactField label="Processing Time" value={metadataValue(projectMetadata, 'processing_time', 'processing_time_ms', 'duration_ms')} />
      <ArtifactField label="Workspace ID" value={metadataValue(projectMetadata, 'workspace_id')} />
      <ArtifactField label="Workspace Path" value={project.storage_path} />
      <ArtifactField label="Project Root" value={metadataValue(projectMetadata, 'project_root', 'root_path')} />
      <ArtifactField label="ZIP File Name" value={metadataValue(projectMetadata, 'zip_file_name', 'archive_name', 'file_name')} />
      <ArtifactField label="ZIP Size" value={metadataValue(projectMetadata, 'zip_size', 'archive_size', 'upload_size')} />
      <ArtifactField label="Extracted Size" value={metadataValue(projectMetadata, 'extracted_size')} />
      <ArtifactField label="Total Files" value={metadataValue(projectMetadata, 'total_files', 'file_count')} />
      <ArtifactField label="Total Directories" value={metadataValue(projectMetadata, 'total_directories', 'directory_count')} />
      <ArtifactField label="Source File Count" value={metadataValue(projectMetadata, 'source_file_count')} />
      <ArtifactField label="Configuration File Count" value={metadataValue(projectMetadata, 'configuration_file_count')} />
      <ArtifactField label="Test File Count" value={metadataValue(projectMetadata, 'test_file_count')} />
      <ArtifactField label="Ignored File Count" value={metadataValue(projectMetadata, 'ignored_file_count')} />
      <ArtifactField label="Detected Languages" value={metadataValue(projectMetadata, 'detected_languages')} />
      <ArtifactField label="Repository Type" value={metadataValue(projectMetadata, 'repository_type')} />
      <ArtifactField label="Entry Point Candidates" value={metadataValue(projectMetadata, 'entry_points', 'entry_point_candidates')} />
      <ArtifactField label="Current Status" value={project.status} />
    </dl><details className="raw-debug-panel"><summary>Complete project setup response</summary><pre>{JSON.stringify(project, null, 2)}</pre></details></section>}
    {reviewStage === 2 && <section className="stage-output-card validation-output"><h2>Project Metadata</h2><dl>
      <ArtifactField label="Project Name" value={project?.name} /><ArtifactField label="Project ID" value={project?.id} /><ArtifactField label="Upload Source" value={project?.source_type} /><ArtifactField label="Upload Time" value={project?.created_at} /><ArtifactField label="Processing Time" value={metadataValue(projectMetadata, 'processing_time_ms')} /><ArtifactField label="Workspace ID" value={metadataValue(projectMetadata, 'workspace_id')} /><ArtifactField label="Workspace Path" value={metadataValue(projectMetadata, 'workspace_path')} /><ArtifactField label="Project Root" value={metadataValue(projectMetadata, 'project_root')} /><ArtifactField label="ZIP File Name" value={metadataValue(projectMetadata, 'zip_file_name')} /><ArtifactField label="ZIP Size" value={metadataValue(projectMetadata, 'zip_size')} /><ArtifactField label="Extracted Size" value={metadataValue(projectMetadata, 'extracted_size')} /><ArtifactField label="Total Files" value={metadataValue(projectMetadata, 'total_files')} /><ArtifactField label="Total Directories" value={metadataValue(projectMetadata, 'total_directories')} /><ArtifactField label="Source File Count" value={metadataValue(projectMetadata, 'source_file_count')} /><ArtifactField label="Configuration File Count" value={metadataValue(projectMetadata, 'configuration_file_count')} /><ArtifactField label="Test File Count" value={metadataValue(projectMetadata, 'test_file_count')} /><ArtifactField label="Ignored File Count" value={metadataValue(projectMetadata, 'ignored_file_count')} /><ArtifactField label="Detected Languages" value={metadataValue(projectMetadata, 'detected_languages')} /><ArtifactField label="Repository Type" value={metadataValue(projectMetadata, 'repository_type')} /><ArtifactField label="Entry Point Candidates" value={metadataValue(projectMetadata, 'entry_point_candidates')} /><ArtifactField label="Current Status" value={project?.status} />
    </dl><details className="raw-debug-panel"><summary>View raw project JSON</summary><pre>{project ? JSON.stringify(project, null, 2) : unavailable}</pre></details><h2>Repository Overview</h2><dl>
      <ArtifactField label="Primary Language" value={dependencyAnalysis.primary_language} />
      <ArtifactField label="Secondary Languages" value={dependencyAnalysis.secondary_languages} />
      <ArtifactField label="Backend Framework" value={dependencyAnalysis.backend_framework} />
      <ArtifactField label="Frontend Framework" value={dependencyAnalysis.frontend_framework} />
      <ArtifactField label="Runtime" value={dependencyAnalysis.runtime} />
      <ArtifactField label="Repository Type" value={dependencyAnalysis.repository_type ?? metadataValue(projectMetadata, 'repository_type')} />
      <ArtifactField label="Architecture Style" value={dependencyAnalysis.architecture_style ?? 'Unknown'} />
      <ArtifactField label="Entry Point" value={dependencyAnalysis.entry_points ?? entryPoints} />
      <ArtifactField label="Dependency Count" value={dependencyAnalysis.dependency_count} />
      <ArtifactField label="Module Count" value={dependencyAnalysis.module_count} />
      <ArtifactField label="Source File Count" value={dependencyAnalysis.source_file_count} />
      <ArtifactField label="Configuration Files" value={dependencyAnalysis.configuration_files ?? configurationFiles} />
      <ArtifactField label="Test Files" value={dependencyAnalysis.test_file_count} />
      <ArtifactField label="Dependency Status" value={dependency?.status} />
    </dl><h2>Repository Analysis</h2>{Object.keys(dependencyGroups).length ? <div className="dependency-groups">{Object.entries(dependencyGroups).map(([group, items]) => <section key={group}><h3>{group}</h3><ul className="artifact-list">{items.map((item) => <li key={item}>{item}</li>)}</ul></section>)}</div> : <p>None detected</p>}
    <h2>Project Structure</h2><dl><ArtifactField label="Entry Point" value={dependencyAnalysis.entry_points} /><ArtifactField label="Architecture Flow" value={dependencyAnalysis.project_structure} /><ArtifactField label="Detected Modules / Packages" value={dependencyAnalysis.modules} /></dl>
    <h2>Security Analysis</h2><dl>
      <ArtifactField label="Scan Status" value={securityScan?.status} />
      <ArtifactField label="Rules Executed" value={securityScan?.summary?.rules_executed ?? 'Unknown'} />
      <ArtifactField label="Files Scanned" value={securityScan?.summary?.files_scanned} />
      <ArtifactField label="Findings Count" value={securityScan?.summary?.total_findings} />
      <ArtifactField label="Engine" value={securityScan?.summary?.engine} />
      <ArtifactField label="Engine Version" value={securityScan?.summary?.engine_version} />
      <ArtifactField label="Duration" value={securityScan?.summary?.duration_ms == null ? undefined : `${securityScan.summary.duration_ms} ms`} />
      <ArtifactField label="Critical" value={securityScan?.summary?.by_severity?.CRITICAL ?? 0} />
      <ArtifactField label="High" value={securityScan?.summary?.by_severity?.HIGH ?? securityScan?.summary?.by_severity?.ERROR ?? 0} />
      <ArtifactField label="Medium" value={securityScan?.summary?.by_severity?.MEDIUM ?? securityScan?.summary?.by_severity?.WARNING ?? 0} />
      <ArtifactField label="Low" value={securityScan?.summary?.by_severity?.LOW ?? securityScan?.summary?.by_severity?.INFO ?? 0} />
    </dl><h3>Security Findings</h3>{securityScan?.findings.length ? <div className="finding-debug-list">{securityScan.findings.map((finding) => <article key={finding.id}><dl>
      <ArtifactField label="Severity" value={finding.severity} />
      <ArtifactField label="Rule ID" value={finding.rule_id} />
      <ArtifactField label="Rule Name" value={metadataValue(finding.metadata, 'rule_name', 'name', 'short_name') ?? readableRuleName(finding.rule_id)} />
      <ArtifactField label="File" value={finding.file} />
      <ArtifactField label="Line" value={finding.line} />
      <ArtifactField label="Message" value={finding.message} />
      <ArtifactField label="Recommendation" value={findingRecommendation(finding.metadata, finding.message)} />
      <ArtifactField label="Likelihood" value={metadataValue(finding.metadata, 'likelihood')} />
      <ArtifactField label="Impact" value={metadataValue(finding.metadata, 'impact')} />
      <ArtifactField label="Confidence" value={metadataValue(finding.metadata, 'confidence')} />
      <ArtifactField label="CWE" value={finding.cwe} />
      <ArtifactField label="OWASP" value={finding.owasp} />
      <ArtifactField label="Reference Links" value={metadataValue(finding.metadata, 'references', 'reference', 'source-rule-url')} />
      <ArtifactField label="Finding Metadata" value={finding.metadata} />
    </dl></article>)}</div> : <p>{unavailable}</p>}
    <details className="raw-debug-panel"><summary>View Raw Semgrep JSON</summary><pre>{securityScan?.summary?.raw_semgrep_json ? JSON.stringify(securityScan.summary.raw_semgrep_json, null, 2) : unavailable}</pre></details>
    <h2>Analysis Summary</h2><ul className="stage-summary"><li>✓ Repository analysis completed</li><li>✓ Security analysis completed</li><li>✓ {securityScan?.summary?.files_scanned ?? 0} files scanned</li><li>✓ {Number(dependencyAnalysis.dependency_count ?? 0)} dependencies detected</li><li>✓ {securityScan?.summary?.total_findings ?? 0} security findings</li></ul>
    <details className="raw-debug-panel"><summary>Complete repository analysis response</summary><pre>{dependency ? JSON.stringify(dependency, null, 2) : unavailable}</pre></details></section>}
    {reviewStage === 3 && understanding && stage3 && <section className="stage3-analysis">
      <button className="stage3-analysis-head" aria-expanded={stage3Open} onClick={() => setStage3Open((open) => !open)}><span><Code2 size={18} /><strong>Test Target Analysis</strong></span>{stage3Open ? <ChevronUp size={18} /> : <ChevronDown size={18} />}</button>
      {stage3Open && <div className="stage3-analysis-body">
        <div className="stage3-analysis-grid">{stage3Groups.map(([label, items]) => <div key={label}><span>{label}</span><strong>{items.length}</strong>{items.length > 0 && <small>{items.slice(0, 8).map((item, index) => stage3ItemLabel(label, item, index)).join(' · ')}{items.length > 8 ? ` · +${items.length - 8} more` : ''}</small>}</div>)}</div>
        <h3>Functions and Source Locations</h3><div className="stage3-source-list">{productionFunctions.map((item, index) => <div key={`${projectRelativePath(item.file)}-${String(item.qualified_name ?? item.name)}-${index}`}><strong>{String(item.qualified_name ?? item.name ?? `Function ${index + 1}`)}</strong><small>{projectRelativePath(item.file)}</small></div>)}</div>
        <h3>Classes and Origins</h3><div className="stage3-source-list">{classRecords.length ? classRecords.map((item, index) => <div key={`${projectRelativePath(item.file)}-${String(item.qualified_name ?? item.name)}-${index}`}><strong>{String(item.qualified_name ?? item.name ?? `Class ${index + 1}`)}</strong><small>{projectRelativePath(item.file)}</small></div>) : <p>None detected</p>}</div>
        <h3>API Endpoints and Origins</h3><div className="stage3-source-list">{endpointRecords.length ? endpointRecords.map((item, index) => <div key={`${projectRelativePath(item.file)}-${String(item.method)}-${String(item.route)}-${index}`}><strong>{String(item.method ?? 'HTTP')} {String(item.route ?? 'Unknown route')}</strong><small>{projectRelativePath(item.file)}</small></div>) : <p>None detected</p>}</div>
        <h3>Request Models and Origins</h3><div className="stage3-source-list">{requestModels.length ? requestModels.map((item, index) => <div key={`request-${index}`}><strong>{item.request_model ?? item.request_type}</strong><small>{projectRelativePath(item.file)}</small></div>) : <p>None detected</p>}</div>
        <h3>Response Models and Origins</h3><div className="stage3-source-list">{responseModels.length ? responseModels.map((item, index) => <div key={`response-${index}`}><strong>{item.response_model ?? item.response_type}</strong><small>{projectRelativePath(item.file)}</small></div>) : <p>None detected</p>}</div>
        <h3>Unique Imports</h3><p><strong>{uniqueImports.length} total unique imports</strong></p>{uniqueImports.length ? <ul className="stage3-value-list">{uniqueImports.map((item) => <li key={item}>{item}</li>)}</ul> : <p>None detected</p>}
        <h3>Exceptions</h3>{exceptionValues.length ? <ul className="stage3-value-list">{exceptionValues.map((item) => <li key={item}>{item}</li>)}</ul> : <p>None detected</p>}
        <h3>Ignored Test Files</h3>{ignoredTestFiles.length ? <ul className="stage3-value-list">{ignoredTestFiles.map((file) => <li key={file}><strong>{file}</strong><small>Existing repository test file</small></li>)}</ul> : <p>None detected</p>}
        <h3>Repository Behavior</h3>{behaviorRows.length ? <div className="stage3-behavior-list">{behaviorRows.map((item, index) => <article key={`${item.file}-${item.name}-${index}`}><strong>{item.name}</strong><small>{item.file}</small>{item.calls.length > 0 && <p><b>Calls:</b> {item.calls.join(', ')}</p>}{item.returns.length > 0 && <p><b>Returns:</b> {item.returns.join(', ')}</p>}{item.exceptions.length > 0 && <p><b>Exceptions:</b> {item.exceptions.join(', ')}</p>}{item.dependencies.length > 0 && <p><b>Dependencies:</b> {item.dependencies.join(', ')}</p>}{item.sideEffects.length > 0 && <p><b>Side effects / writes:</b> {item.sideEffects.join(', ')}</p>}</article>)}</div> : <p>Not Available</p>}
        <details className="raw-debug-panel"><summary>Function Call Relationships</summary>{callGraph.length ? <div className="stage3-call-list">{callGraph.map((edge, index) => <div key={`${String(edge.caller)}-${String(edge.callee)}-${index}`}><strong>{String(edge.caller ?? 'Unknown caller')}</strong><span>↓</span><strong>{String(edge.callee ?? 'Unknown callee')}</strong><small>{projectRelativePath(edge.file)}</small></div>)}</div> : <p>None detected</p>}</details>
        <h3>Test Target Eligibility</h3><p><strong>{eligibleFunctions.length} / {productionFunctions.length} eligible</strong></p>{excludedFunctions.length > 0 && <><p>Excluded:</p><ul className="stage3-value-list">{excludedFunctions.map((item, index) => <li key={`${item.file}-${item.name}-${index}`}><strong>{item.name}</strong> — {item.reason}<small>{item.file}</small></li>)}</ul></>}
        <h3>Test Target Summary</h3><ul className="stage-summary"><li>✓ {stage3.modules?.length ?? 0} modules analyzed</li><li>✓ {productionFunctions.length} production functions discovered</li><li>✓ {stage3.classes?.length ?? 0} classes discovered</li><li>✓ {stage3.api_endpoints?.length ?? 0} API endpoints discovered</li><li>✓ {productionTargets.length} executable unit-test targets</li><li>✓ {ignoredTestFiles.length} existing repository test files excluded from the validation view</li><li>✓ {stage3.security_findings?.length ?? 0} security findings carried forward</li><li>{stage3.repository_behavior ? '✓ Repository behavior extracted' : 'Repository behavior pending'}</li><li>{stage3.call_graph ? '✓ Call graph generated' : 'Call graph pending'}</li><li>{stage3.dependency_graph ? '✓ Dependency graph generated' : 'Dependency graph pending'}</li><li>Ready for unit test generation</li></ul>
        <div className="stage3-actions"><Button variant="secondary" onClick={() => setJsonOpen((open) => !open)}><Eye size={15} /> View JSON</Button><Button variant="secondary" onClick={() => void copyStage3()}><Clipboard size={15} /> {copied ? 'Copied' : 'Copy JSON'}</Button><Button variant="secondary" onClick={() => download(`${job.projectName}-stage-3-response`, understanding)}><Download size={15} /> Download JSON</Button></div>
        {jsonOpen && <pre className="stage3-json">{rawStage3Json}</pre>}
      </div>}
    </section>}
    {reviewStage === 4 && stage4Generation && <section className="stage-output-card stage4-validation"><h2>Generated Unit Tests</h2><div className="metrics three"><MetricCard icon={TestTube2} title="Generated tests" value={stage4Generation.total_after_deduplication} helper={`${duplicateTestsRemoved} duplicates removed`} /><MetricCard icon={Gauge} title="Production coverage" value={`${stage4Coverage}%`} helper={`${coveredTargets.length} of ${coverageTargets.length} targets`} /><MetricCard icon={Clock3} title="Generation duration" value={stage4Duration} helper="Unit test generation time" /></div>
      <h3>Stage Statistics</h3><dl><ArtifactField label="Production Functions" value={coverageTargets.length} /><ArtifactField label="Covered Production Targets" value={coveredTargets.length} /><ArtifactField label="Coverage Percentage" value={`${stage4Coverage}%`} /><ArtifactField label="Generated Tests" value={stage4Generation.total_after_deduplication} /><ArtifactField label="Average Tests / Function" value={coverageTargets.length ? (stage4Generation.total_after_deduplication / coverageTargets.length).toFixed(2) : '0.00'} /><ArtifactField label="Functions with Boundary Tests" value={uniqueCategoryTargets(/boundary/i)} /><ArtifactField label="Functions with Exception Tests" value={uniqueCategoryTargets(/exception/i)} /><ArtifactField label="Security Regression Tests" value={categoryTotal(/security/i)} /><ArtifactField label="Duplicate Tests Removed" value={duplicateTestsRemoved} /><ArtifactField label="Category Distribution" value={stage4Categories} /></dl>
      <h3>Unit Test Summary</h3><ul className="stage-summary"><li>✓ Generation completed</li><li>✓ {stage4Generation.total_after_deduplication} tests generated</li><li>✓ {coveredTargets.length} production targets covered</li><li>✓ {stage4Coverage}% production coverage</li><li>✓ {categoryTotal(/positive/i)} positive tests</li><li>✓ {categoryTotal(/boundary/i)} boundary tests</li><li>✓ {categoryTotal(/exception/i)} exception tests</li><li>✓ {categoryTotal(/security/i)} security tests</li><li>✓ {duplicateTestsRemoved} duplicates removed</li><li>✓ Deterministic generation</li><li>✓ Ready for AI verification</li></ul>
      <h3>Test Categories</h3><ul className="stage3-value-list">{Object.entries(stage4Categories).map(([category, count]) => <li key={category}><strong>{category}</strong> — {count}</li>)}</ul>
      <h3>Generated Test Cases</h3><div className="stage4-test-list">{stage4Tests.map((test) => {
        const traceability = test.traceability ?? {}
        const source = projectRelativePath(test.unit_test?.file ?? traceability.file ?? traceability.source_file ?? traceability.target_file)
        const targetSymbol = symbolName(test.unit_test?.symbol ?? traceability.symbol ?? traceability.target ?? traceability.target_symbol)
        const fn = productionFunctions.find((item) => symbolName(item.name ?? item.qualified_name) === targetSymbol && (projectRelativePath(item.file) === source || source === unavailable))
        const calls = stringValues(fn?.calls).length ? stringValues(fn?.calls) : callGraph.filter((edge) => symbolName(edge.caller) === targetSymbol).map((edge) => String(edge.callee ?? '')).filter(Boolean)
        const endpoint = endpointRecords.find((item) => symbolName(item.handler) === targetSymbol)
        const dependencies = stringValues(endpoint?.dependencies)
        const exceptions = flattenExceptions(fn?.exceptions ?? behaviorExceptions[String(fn?.qualified_name ?? targetSymbol)] ?? behaviorExceptions[targetSymbol])
        const sideEffects = stringValues(fn?.side_effects).length ? stringValues(fn?.side_effects) : stringValues(behaviorSideEffects[String(fn?.qualified_name ?? targetSymbol)] ?? behaviorSideEffects[targetSymbol])
        const sourceResolved = source !== unavailable
        const symbolResolved = Boolean(fn && targetSymbol)
        const behaviorResolved = Boolean(fn && (calls.length || fn.return_type || exceptions.length || dependencies.length || sideEffects.length))
        const confidence = sourceResolved && symbolResolved && behaviorResolved && callGraph.length ? 'High' : sourceResolved && symbolResolved ? 'Medium' : 'Low'
        const fixtures = test.unit_test?.fixture_names ?? []
        const patches = [...new Set((test.unit_test?.patches ?? []).map(patchLabel))]
        const code = test.unit_test?.generated_code ?? ''
        const indicators = generatedCodeIndicators(code, test.category, Boolean(test.unit_test?.is_async))
        const relatedSecurity = (stage3?.security_findings ?? []).filter((finding) => {
          const findingFile = projectRelativePath(finding.file)
          return sourceResolved && findingFile !== unavailable && (findingFile === source || findingFile.endsWith(`/${source}`) || source.endsWith(`/${findingFile}`))
        })
        return <article key={test.id}><strong>{test.title}</strong><small>{test.id}</small><p>{test.description}</p><div className="quality-badges">{indicators.mocks && <Badge tone="success">✓ Uses mocks</Badge>}{indicators.assertions && <Badge tone="success">✓ Has assertions</Badge>}{indicators.exception && <Badge>✓ Exception tested</Badge>}{indicators.boundary && <Badge>✓ Boundary tested</Badge>}{indicators.security && <Badge tone="warning">✓ Security regression</Badge>}{indicators.async && <Badge>✓ Async</Badge>}{indicators.parameterized && <Badge>✓ Parameterized</Badge>}</div><dl><ArtifactField label="Category" value={test.category} /><ArtifactField label="Target Function" value={targetSymbol || 'Fallback target'} /><ArtifactField label="Source" value={sourceResolved ? source : 'Source resolved through fallback metadata'} /><ArtifactField label="Confidence" value={confidence} /><ArtifactField label="Fixtures" value={fixtures.length ? fixtures : 'No fixtures required'} /><ArtifactField label="Patch Targets" value={patches.length ? patches : 'No patches required'} /></dl>
          <h4>Behavior Verified</h4><dl><ArtifactField label="Calls" value={calls.length ? calls : 'No calls detected'} /><ArtifactField label="Dependencies" value={dependencies.length ? dependencies : 'No dependencies detected'} /><ArtifactField label="Exceptions" value={exceptions.length ? exceptions : 'No exceptions detected'} /><ArtifactField label="Return Type" value={fn?.return_type ?? 'No return value declared'} /><ArtifactField label="Side Effects" value={sideEffects.length ? sideEffects : 'No side effects detected'} /></dl>
          <h4>Deterministic Evidence</h4><dl><ArtifactField label="Source" value={sourceResolved ? source : 'Fallback source metadata'} /><ArtifactField label="Function" value={targetSymbol || 'Fallback target'} /><ArtifactField label="Calls" value={calls.length ? calls : 'No calls detected'} /><ArtifactField label="Returns" value={fn?.return_type ?? 'No return value declared'} /><ArtifactField label="Raises" value={exceptions.length ? exceptions : 'No exceptions detected'} /><ArtifactField label="Side Effects" value={sideEffects.length ? sideEffects : 'No side effects detected'} /></dl>
          {relatedSecurity.length > 0 && <><h4>Security Source</h4><div className="security-trace-list">{relatedSecurity.map((finding, index) => <dl key={`${String(finding.rule_id)}-${index}`}><ArtifactField label="Semgrep Rule" value={finding.rule_id} /><ArtifactField label="Severity" value={finding.severity} /><ArtifactField label="Reason" value={finding.message ?? readableRuleName(String(finding.rule_id ?? 'Security finding'))} /><ArtifactField label="Origin" value={`${projectRelativePath(finding.file)}${finding.line ? `:${finding.line}` : ''}`} /></dl>)}</div></>}
          <details className="raw-debug-panel"><summary>Generated Pytest Preview</summary><div className="pytest-preview"><p><strong>Arrange:</strong> {fixtures.length ? `Fixtures: ${fixtures.join(', ')}` : 'No fixtures required'}; {patches.length ? `Mocks: ${patches.join(', ')}` : 'no mocks required'}</p><p><strong>Act:</strong> Execute {targetSymbol || 'generated target'}</p><p><strong>Assert:</strong> {indicators.assertions ? 'Generated assertions present' : 'No explicit assert statement detected'}</p><p><strong>Mocks:</strong> {indicators.mocks ? 'Mock usage detected' : 'No mock usage required'}</p><p><strong>Assertions:</strong> {indicators.exception ? 'Exception outcome verified' : 'Return behavior verified'}</p><pre>{code || 'Generated unit test code is not available yet.'}</pre></div></details>
        </article>
      })}</div>
      <div className="stage3-actions"><Button variant="secondary" disabled={!generatedPytest} onClick={() => downloadText(`${job.projectName}-generated-tests`, generatedPytest)}><Download size={15} /> Export Pytest Suite</Button><Button variant="secondary" onClick={() => download(`${job.projectName}-unit-test-generation`, stage4Generation)}><Download size={15} /> Export Generation JSON</Button></div>
    </section>}
    {reviewStage === 5 && stage5Verification && stage4Generation && <section className="stage-output-card stage5-validation"><h2>AI Verification</h2>
      <h3>AI Verification Summary</h3><div className="metrics three"><MetricCard icon={ShieldCheck} title="Verified Tests" value={stage5Verification.summary.verified} helper="Behavior confirmed" /><MetricCard icon={CircleAlert} title="Partially Verified" value={stage5Verification.summary.partial} helper="Manual review recommended" /><MetricCard icon={X} title="Failed Verification" value={stage5Verification.summary.failed} helper="Behavior mismatch" /><MetricCard icon={Gauge} title="Verification Coverage" value={`${verificationCoverage}%`} helper={`${verificationTotal} tests evaluated`} /><MetricCard icon={TrendingUp} title="Average Confidence" value={`${averageConfidence}%`} helper="AI verification confidence" /><MetricCard icon={Clock3} title="Verification Duration" value={verificationDuration} helper="AI verification time" /></div>
      <h3>Test-by-Test Verification</h3><div className="stage5-test-list">{stage4Tests.map((test) => {
        const result = verificationByTest.get(test.id)
        const traceability = test.traceability ?? {}
        const source = projectRelativePath(test.unit_test?.file ?? traceability.file ?? traceability.source_file)
        const target = symbolName(test.unit_test?.symbol ?? traceability.symbol ?? traceability.target ?? traceability.target_symbol)
        const fn = productionFunctions.find((item) => symbolName(item.name ?? item.qualified_name) === target && (projectRelativePath(item.file) === source || source === unavailable))
        const calls = stringValues(fn?.calls).length ? stringValues(fn?.calls) : callGraph.filter((edge) => symbolName(edge.caller) === target).map((edge) => String(edge.callee ?? '')).filter(Boolean)
        const endpoint = endpointRecords.find((item) => symbolName(item.handler) === target)
        const exceptions = flattenExceptions(fn?.exceptions ?? behaviorExceptions[String(fn?.qualified_name ?? target)] ?? behaviorExceptions[target])
        const sideEffects = stringValues(fn?.side_effects).length ? stringValues(fn?.side_effects) : stringValues(behaviorSideEffects[String(fn?.qualified_name ?? target)] ?? behaviorSideEffects[target])
        const security = (stage3?.security_findings ?? []).filter((finding) => projectRelativePath(finding.file) === source)
        const confidence = result ? (result.confidence <= 1 ? result.confidence * 100 : result.confidence) : 0
        const reason = result?.findings.find((finding) => finding.status !== 'Verified' && finding.check !== 'duplicate')?.detail ?? result?.findings.find((finding) => finding.status !== 'Verified')?.detail ?? result?.findings[0]?.detail ?? (result?.status === 'Verified' ? 'Assertions match the source behavior and deterministic evidence.' : 'Verification result unavailable.')
        const inferredReturn = traceability.return_type ?? traceability.inferred_return ?? traceability.returns
        const returnInformation = fn?.return_type ? `Explicit return annotation: ${String(fn.return_type)}` : inferredReturn ? `Inferred return: ${String(inferredReturn)}` : fn?.has_return === false ? 'No return statement detected' : 'No return annotation; return behavior is inferred from source evidence'
        const expectedException = test.unit_test?.expected_exception ?? (exceptions.length ? exceptions.join(', ') : 'No exception declared by repository analysis')
        return <article key={test.id}><header><div><strong>{test.id}</strong><small>{test.title}</small></div><Badge tone={tone(result?.status)}>{result?.status ?? 'Failed'}</Badge></header><dl><ArtifactField label="Target Function" value={target || 'Unresolved target'} /><ArtifactField label="Source File" value={source} /><ArtifactField label="Category" value={test.category} /><ArtifactField label="Confidence" value={`${Math.round(confidence * 100) / 100}%`} /><ArtifactField label="Reason" value={reason} /></dl>
          <h4>Source Evidence</h4><dl><ArtifactField label="Function" value={target || 'Unresolved target'} /><ArtifactField label="Calls" value={calls.length ? calls : 'No calls detected'} /><ArtifactField label="Returns" value={returnInformation} /><ArtifactField label="Exceptions" value={exceptions.length ? exceptions : 'No exceptions declared by repository analysis'} /><ArtifactField label="Dependencies" value={stringValues(endpoint?.dependencies).length ? stringValues(endpoint?.dependencies) : 'No dependencies detected'} /><ArtifactField label="Side Effects" value={sideEffects.length ? sideEffects : 'No side effects detected'} /></dl>
          <h4>Assertion Validation</h4><div className="assertion-comparison"><div><strong>Expected return / behavior</strong><p>{test.expected_results.join('; ')}</p></div><div><strong>Observed verification</strong><p>{result?.findings.map((finding) => `${finding.check}: ${finding.detail}`).join('; ') || 'No verification findings returned.'}</p></div><div><strong>Expected exception</strong><p>{expectedException}</p></div><div><strong>Observed exceptions</strong><p>{exceptions.join(', ') || 'No source exceptions detected'}</p></div><div><strong>Expected side effects</strong><p>{sideEffects.join(', ') || 'No side effects expected'}</p></div><div><strong>Observed evidence</strong><p>{result?.evidence.map((item) => `${projectRelativePath(item.file)}${item.line ? `:${item.line}` : ''} — ${item.detail}`).join('; ') || 'No direct evidence returned'}</p></div></div>
          <h4>Traceability</h4><div className="traceability-chain"><strong>{test.id}</strong><span>↓</span><strong>{target || 'Unresolved Stage 3 function'}</strong>{security.map((finding, index) => <span className="trace-step" key={`${String(finding.rule_id)}-${index}`}>↓<strong>{readableRuleName(String(finding.rule_id ?? 'Security finding'))}</strong></span>)}<span>↓</span><strong>{source}</strong></div>
        </article>
      })}</div>
      <h3>Security Test Verification</h3>{(stage3?.security_findings ?? []).length ? <div className="security-verification-list">{(stage3?.security_findings ?? []).map((finding, index) => { const source = projectRelativePath(finding.file); const matchingTests = securityTests.filter((test) => projectRelativePath(test.unit_test?.file ?? test.traceability?.file ?? test.traceability?.source_file) === source); const verified = verifiedCategoryCount(matchingTests); const partial = matchingTests.filter((test) => verificationByTest.get(test.id)?.status === 'Partial').length; const failed = matchingTests.filter((test) => verificationByTest.get(test.id)?.status === 'Failed').length; const coverage = matchingTests.length ? Math.round(((verified + (partial * 0.5)) / matchingTests.length) * 10000) / 100 : 0; return <dl key={`${String(finding.rule_id)}-${index}`}><ArtifactField label="Rule" value={finding.rule_id} /><ArtifactField label="Affected Function" value={finding.function ?? finding.symbol ?? 'File-level finding'} /><ArtifactField label="Generated Security Tests" value={matchingTests.map((test) => test.id)} /><ArtifactField label="Verified / Partial / Failed" value={`${verified} / ${partial} / ${failed}`} /><ArtifactField label="Verification Result" value={matchingTests.length && verified === matchingTests.length ? 'Verified' : matchingTests.length ? 'Review Required' : 'No matching security test'} /><ArtifactField label="Semantic Coverage" value={`${coverage}%`} /></dl> })}</div> : <p>No repository security findings required dedicated unit tests.</p>}
      <h3>Verification Findings</h3>{groupedVerificationFindings.length ? <div className="verification-findings">{groupedVerificationFindings.map((finding) => <details key={`${finding.check}-${finding.detail}`}><summary><strong>{finding.check.replaceAll('_', ' ')}</strong> — {finding.testIds.length} affected test{finding.testIds.length === 1 ? '' : 's'}</summary><dl><ArtifactField label="Severity" value={finding.status === 'Failed' ? 'High' : 'Medium'} /><ArtifactField label="Problem" value={finding.detail} /><ArtifactField label="Affected Tests" value={finding.testIds} /><ArtifactField label="Recommendation" value={verificationRecommendation(finding.check)} /></dl></details>)}</div> : <p>No verification problems detected.</p>}
      <h3>Quality Metrics</h3><dl><ArtifactField label="Semantic Correctness" value={`${semanticCorrectness}%`} /><ArtifactField label="Verification Pass Rate" value={`${verificationCoverage}%`} /><ArtifactField label="Traceability" value={`${metricPercent(tracedResults, verificationTotal)}%`} /><ArtifactField label="Behavior Match" value={`${metricPercent(behaviorChecks.filter((finding) => finding.status === 'Verified').length, behaviorChecks.length)}%`} /><ArtifactField label="Exception Coverage" value={`${metricPercent(verifiedCategoryCount(exceptionTests), exceptionTests.length)}%`} /><ArtifactField label="Security Coverage" value={`${securitySemanticCoverage}% (${securityStatusCounts.Verified ?? 0} verified, ${securityStatusCounts.Partial ?? 0} partial, ${securityStatusCounts.Failed ?? 0} failed)`} /><ArtifactField label="Boundary Coverage" value={`${metricPercent(verifiedCategoryCount(boundaryTests), boundaryTests.length)}%`} /><ArtifactField label="Duplicate Tests" value={duplicateVerificationCount} /><ArtifactField label="Maintainability" value={`${metricPercent(maintainableTests, stage4Tests.length)}%`} /></dl>
      <div className={`stage5-recommendation ${finalRecommendation === 'READY FOR QUALITY OPTIMIZATION' ? 'ready' : 'review'}`}><strong>{finalRecommendation}</strong><p>{finalRecommendation === 'READY FOR QUALITY OPTIMIZATION' ? 'Every generated test passed semantic verification and is ready for Stage 6.' : finalRecommendation === 'REVIEW REQUIRED' ? 'Some tests are partially verified and should be reviewed before optimization.' : 'At least one generated test does not match the source behavior and should be regenerated.'}</p></div>
      <h3>Downloads</h3><div className="stage3-actions"><Button variant="secondary" onClick={() => download(`${job.projectName}-verified-tests`, stage4Tests.filter((test) => verificationByTest.get(test.id)?.status === 'Verified'))}><Download size={15} /> Verified Tests JSON</Button><Button variant="secondary" onClick={() => download(`${job.projectName}-verification-report`, stage5Verification)}><Download size={15} /> Verification Report JSON</Button><Button variant="secondary" onClick={() => download(`${job.projectName}-verification-summary`, { ...stage5Verification.summary, verification_coverage: verificationCoverage, average_confidence: averageConfidence, duration: verificationDuration, recommendation: finalRecommendation })}><Download size={15} /> Verification Summary</Button></div>
    </section>}
    {reviewStage === 6 && <section className="stage-output-card validation-output"><h2>Stage 6 — Quality Optimization</h2>{quality ? <><div className="metrics three"><MetricCard icon={Gauge} title="Overall quality" value={`${quality.final_score}%`} helper={`${quality.improvement_metrics.score_delta >= 0 ? '+' : ''}${quality.improvement_metrics.score_delta} points`} /><MetricCard icon={TestTube2} title="Optimized tests" value={quality.optimized_test_suite.length} helper={`${quality.iterations} iteration${quality.iterations === 1 ? '' : 's'}`} /><MetricCard icon={ShieldCheck} title="Security score" value={`${quality.quality_evaluation.dimension_scores.security ?? quality.quality_evaluation.dimension_scores.security_coverage ?? unavailable}${typeof (quality.quality_evaluation.dimension_scores.security ?? quality.quality_evaluation.dimension_scores.security_coverage) === 'number' ? '%' : ''}`} helper="Security quality dimension" /></div><dl><ArtifactField label="Coverage" value={quality.quality_evaluation.dimension_scores.coverage} /><ArtifactField label="Duplicates" value={duplicateTestsRemoved} /><ArtifactField label="Maintainability" value={quality.quality_evaluation.dimension_scores.maintainability} /><ArtifactField label="Stopping Reason" value={quality.stopping_reason} /><ArtifactField label="Threshold Met" value={quality.quality_evaluation.threshold_met} /><ArtifactField label="Recommendations" value={quality.quality_evaluation.recommendations} /></dl><details className="raw-debug-panel"><summary>Complete Stage 6 output</summary><pre>{JSON.stringify(quality, null, 2)}</pre></details></> : <Empty title="Quality output pending" detail="Stage 6 has not produced a persisted result yet." />}</section>}
    {reviewStage === 7 && <section className="stage-output-card validation-output"><h2>Stage 7 — Runtime Validation</h2>{runtimeReport ? <><div className="metrics three"><MetricCard icon={Gauge} title="Pass rate" value={`${runtimeReport.pass_rate}%`} helper={`${runtimeReport.summary.passed} passed`} /><MetricCard icon={CircleAlert} title="Failed tests" value={runtimeReport.summary.failed} helper={`${runtimeReport.summary.skipped} skipped`} /><MetricCard icon={Clock3} title="Duration" value={`${runtimeReport.duration_ms} ms`} helper={runtimeReport.status} /></div><h3>Execution Order</h3><ol className="runtime-evidence-list">{runtimeReport.results.map((result, index) => <li key={result.test_case_id}><strong>{index + 1}. {result.test_case_id}</strong><Badge tone={result.runtime_status === 'Passed' ? 'success' : result.runtime_status === 'Failed' ? 'danger' : 'warning'}>{result.runtime_status}</Badge><small>{result.execution_time_ms} ms</small>{result.assertion_failure && <p>{result.assertion_failure}</p>}<details><summary>Runtime evidence and logs</summary><pre>{JSON.stringify({ expected: result.expected_result, actual: result.actual_result, logs: result.logs }, null, 2)}</pre></details></li>)}</ol></> : <Empty title="Runtime results pending" detail="Stage 7 runtime evidence will appear here as soon as validation completes." />}</section>}
    </>}
    {stageTab === 'logs' && <section className="stage-logs"><h2>{reviewStage === currentStageNumber ? 'Live' : 'Persisted'} Stage {reviewStage} Logs</h2><pre>{reviewStage === currentStageNumber && job.logs?.length ? job.logs.join('\n') : 'No additional stage logs are available.'}</pre></section>}
    {stageTab === 'raw' && <section className="raw-stage-view"><details open><summary>Complete Stage {reviewStage} JSON</summary><pre>{rawStageArtifact ? JSON.stringify(rawStageArtifact, null, 2) : 'Stage output has not been produced yet.'}</pre></details></section>}
    </div></details></main></div>
    {job.status === 'paused' && project && (job.currentStage === 'stage_4' ? <div className="stage-approval-actions"><Button onClick={() => state.continuePipeline(project)}><ArrowRight size={15} /> Verify Generated Tests</Button></div> : job.currentStage === 'stage_5' ? <div className="stage-approval-actions"><Button onClick={() => state.continuePipeline(project)}><ArrowRight size={15} /> Optimize Test Quality</Button></div> : job.currentStage === 'stage_6' ? <div className="stage-approval-actions"><Button onClick={() => state.continuePipeline(project)}><ArrowRight size={15} /> Run Runtime Validation</Button></div> : job.nextStage ? <div className="stage-approval-actions"><Button onClick={() => state.approveNextStage(project)}><ArrowRight size={15} /> Continue Analysis</Button></div> : null)}
    <section className="activity-timeline"><div className="timeline-heading"><div><h2>AI activity</h2><p>Live milestones from this analysis</p></div>{job.status === 'running' && <span className="thinking"><i /><i /><i /></span>}</div>
      <div className="timeline-list" ref={activityFeedRef}>{visibleActivity.map((activity, index) => <article key={activity.id} className={activity.status}><span className="timeline-marker">{activity.status === 'failed' ? <CircleAlert size={16} /> : activity.status === 'active' ? <Sparkles size={16} /> : <CheckCircle2 size={16} />}</span><div><strong>{activity.label}</strong><p>{activity.detail}</p></div><time>{index === visibleActivity.length - 1 && job.status === 'running' ? 'Just now' : activity.at.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</time></article>)}</div>
      {hiddenActivityCount > 0 && <Button variant="secondary" onClick={() => setShowActivityHistory((visible) => !visible)}>{showActivityHistory ? 'Show latest 100 events' : `Show ${hiddenActivityCount} earlier events`}</Button>}
    </section>
    {job.status === 'failed' && (
      <div style={{ display: 'flex', gap: '12px', marginTop: '16px' }}>
        <Button
          disabled={job.stage.startsWith('Resuming')}
          onClick={() => {
            const project = state.projects.find((p) => p.id === id)
            if (project) {
              if (Number(job.currentStage?.slice(-1) ?? 0) >= 5) state.continuePipeline(project)
              else if (job.currentStage) state.approveNextStage(project)
              else if (job.kind === 'security_scan') state.retrySecurityScan(project)
              else state.resumePipeline(project)
            }
          }}
        >
          {job.stage.startsWith('Resuming') ? 'Resuming...' : 'Retry'}
        </Button>
        {!job.currentStage && <Button
          variant="secondary"
          disabled={job.stage.startsWith('Resuming')}
          onClick={() => {
            const project = state.projects.find((p) => p.id === id)
            if (project) {
              if (job.kind === 'security_scan') state.startSecurityScan(project)
              else state.startPipeline(project)
            }
          }}
        >
          Restart
        </Button>}
        <Button variant="secondary" disabled={job.stage.startsWith('Resuming')} onClick={() => navigate('/projects')}>
          Back to projects
        </Button>
      </div>
    )}
  </div></div>
}

const severityTone = (severity: string) => severity === 'ERROR' || severity === 'CRITICAL' || severity === 'HIGH'
  ? 'danger' as const
  : severity === 'WARNING' || severity === 'MEDIUM'
    ? 'warning' as const
    : 'info' as const

function formatScanDuration(duration?: number | null) {
  if (duration == null) return '—'
  if (duration < 1000) return `${duration} ms`
  return `${(duration / 1000).toFixed(duration < 10_000 ? 1 : 0)} s`
}

export function SecurityReportPage() {
  const { id = '' } = useParams()
  const state = useAppState()
  const navigate = useNavigate()
  useEffect(() => { if (id && state.activeProjectId !== id) state.setActiveProjectId(id) }, [id])
  const project = state.projects.find((item) => item.id === id)
  const scan = state.artifacts.securityScan
  const summary = scan?.summary
  const severities = Object.entries(summary?.by_severity ?? {}).sort(([, left], [, right]) => right - left)
  const proceed = () => {
    if (!project || scan?.status !== 'completed') return
    state.approveNextStage(project)
    navigate(`/processing/${project.id}`)
  }
  useEffect(() => {
    if (!id || state.activeProjectId !== id) return
    void api.latestSecurityScan(id)
      .then((latest) => state.setArtifacts((current) => ({ ...current, securityScan: latest })))
      .catch(() => undefined)
  }, [id, state.activeProjectId])

  if (state.activeProjectId !== id) return <div className="page"><PageHeader title="Security Analysis" subtitle="Loading the selected project." /><Loading /></div>
  if (state.artifactsLoading && !scan) return <div className="page"><PageHeader title="Security Analysis" subtitle="Loading the latest security scan." /><Loading /></div>
  if (!scan) return <div className="page"><PageHeader title="Security Analysis" subtitle="Review security findings that inform unit test generation." /><Empty title="No security analysis found" detail="Generate unit tests for this project to run its security analysis." action={<Button onClick={() => navigate('/projects')}>Back to projects</Button>} /></div>

  return <div className="page">
    <PageHeader
      title="Security Analysis"
      subtitle={project ? `Security findings for ${project.name}.` : 'Repository security analysis results.'}
      action={<div className="header-actions"><Button variant="secondary" onClick={() => download(`${project?.name ?? 'project'}-security-scan`, scan)}><Download size={16} /> Download JSON</Button>{scan.status === 'failed' && project && <Button variant="secondary" onClick={() => { state.approveNextStage(project); navigate(`/processing/${project.id}`) }}>Retry Security Analysis</Button>}<Button disabled={scan.status !== 'completed'} onClick={proceed}>Continue Analysis <ArrowRight size={16} /></Button></div>}
    />
    <div className="metrics">
      <MetricCard icon={ShieldCheck} title="Scan status" value={<Badge tone={tone(scan.status)}>{scan.status}</Badge>} helper={`Progress ${scan.progress_percent}%`} />
      <MetricCard icon={Clock3} title="Duration" value={formatScanDuration(summary?.duration_ms)} helper="Semgrep execution time" />
      <MetricCard icon={FileArchive} title="Files scanned" value={summary?.files_scanned ?? 0} helper={`${summary?.errors ?? 0} scanner errors`} />
      <MetricCard icon={CircleAlert} title="Findings" value={summary?.total_findings ?? scan.findings.length} helper="Total detected issues" />
    </div>
    {scan.error_message && <ErrorNotice message={securityScanErrorMessage(scan.error_message)} />}
    <Section title="Scanner diagnostics" description="Parser issues, unsupported targets, warnings, and genuine scanner failures reported by Semgrep.">
      <div className="security-severity-grid"><div><span>Scanner failures</span><strong>{summary?.errors ?? 0}</strong></div><div><span>Parser issues</span><strong>{summary?.parser_errors ?? 0}</strong></div><div><span>Warnings</span><strong>{summary?.warnings ?? 0}</strong></div><div><span>Informational</span><strong>{summary?.informational ?? 0}</strong></div><div><span>Unsupported</span><strong>{summary?.unsupported_files ?? 0}</strong></div><div><span>Expected skips</span><strong>{summary?.skipped_files ?? 0}</strong></div></div>
      {summary?.diagnostics.length ? <div className="insight-card-list">{summary.diagnostics.map((diagnostic, index) => <div key={`${diagnostic.type}-${diagnostic.path}-${index}`}><CircleAlert size={17} /><div><strong>{diagnostic.level.toUpperCase()} · {diagnostic.type}</strong><small>{diagnostic.category.replaceAll('_', ' ')} · {diagnostic.message}</small>{diagnostic.path && <small>{diagnostic.path}</small>}</div></div>)}</div> : <div className="positive-insight"><ShieldCheck size={18} /><div><strong>No scanner diagnostics</strong><small>{summary?.skipped_files ? `${summary.skipped_files} expected exclusions were applied.` : 'Semgrep completed without parser errors, warnings, or scanner failures.'}</small></div></div>}
    </Section>
    <Section title="Severity summary" description="Findings grouped by Semgrep severity.">
      {severities.length ? <div className="security-severity-grid">{severities.map(([severity, count]) => <div key={severity}><Badge tone={severityTone(severity)}>{severity}</Badge><strong>{count}</strong></div>)}</div> : <div className="positive-insight"><ShieldCheck size={18} /><div><strong>No security findings</strong><small>Semgrep returned no findings for this scan.</small></div></div>}
    </Section>
    <Section title="Findings" description={`${scan.findings.length} persisted finding${scan.findings.length === 1 ? '' : 's'} from the JSON report.`}>
      {scan.findings.length ? <div className="table-card"><div className="table-scroll"><table><thead><tr><th>Severity</th><th>Rule</th><th>Location</th><th>CWE / OWASP</th><th>Message</th></tr></thead><tbody>{scan.findings.map((finding) => <tr key={finding.id}><td><Badge tone={severityTone(finding.severity)}>{finding.severity}</Badge></td><td><strong>{finding.rule_id}</strong></td><td><strong>{finding.file}</strong><small>Line {finding.line}</small></td><td><span>{[...finding.cwe, ...finding.owasp].join(' · ') || '—'}</span></td><td><span>{finding.message}</span></td></tr>)}</tbody></table></div></div> : <Empty title="No findings detected" detail="The scan completed without identifying security findings." />}
    </Section>
  </div>
}

function TestCaseGroups({ tests }: { tests: TestCase[] }) {
  const state = useAppState()
  const verification = new Map(state.artifacts.verification?.results.map((item) => [item.test_case_id, item]))
  const [expanded, setExpanded] = useState<Set<string>>(new Set())
  const [category, setCategory] = useState('all')
  const [priority, setPriority] = useState('all')
  const [status, setStatus] = useState('all')
  const filtered = tests.filter((test) =>
    (category === 'all' || test.category === category)
    && (priority === 'all' || test.priority === priority)
    && (status === 'all' || verification.get(test.id)?.status === status))
  const groups = filtered.reduce<Record<string, TestCase[]>>((all, test) => {
    const group = testGroup(test)
    all[group] = [...(all[group] ?? []), test]
    return all
  }, {})
  const toggle = (id: string) => setExpanded((current) => { const next = new Set(current); if (next.has(id)) next.delete(id); else next.add(id); return next })
  return <div className="test-groups"><div className="test-filters"><label>Category<select value={category} onChange={(event) => setCategory(event.target.value)}><option value="all">All categories</option>{[...new Set(tests.map((test) => test.category))].map((value) => <option key={value}>{value}</option>)}</select></label><label>Priority<select value={priority} onChange={(event) => setPriority(event.target.value)}><option value="all">All priorities</option>{[...new Set(tests.map((test) => test.priority))].map((value) => <option key={value}>{value}</option>)}</select></label><label>Verification<select value={status} onChange={(event) => setStatus(event.target.value)}><option value="all">All statuses</option><option>Verified</option><option>Partial</option><option>Failed</option></select></label><span>{filtered.length} of {tests.length} tests</span></div>{Object.entries(groups).map(([group, groupTests]) => <section className="test-group" key={group}><header><div className="group-icon"><Code2 size={18} /></div><div><h2>{group.replaceAll('_', ' ')}</h2><p>{groupTests.length} test case{groupTests.length === 1 ? '' : 's'}</p></div><Badge>{groupTests.filter((test) => verification.get(test.id)?.status === 'Verified').length} verified</Badge></header><div className="test-card-list">{groupTests.map((test) => { const result = verification.get(test.id); const confidence = confidenceLabel(result?.confidence); const open = expanded.has(test.id); return <article className={`test-card ${open ? 'expanded' : ''}`} key={test.id}><button className="test-card-summary" aria-expanded={open} onClick={() => toggle(test.id)}><span className={`test-status-dot ${result?.status?.toLowerCase() ?? 'pending'}`} /><div><div className="test-title-line"><strong>{test.title}</strong><code>{test.id}</code></div><p>{test.description}</p><div className="test-badges"><Badge tone={tone(result?.status)}>{result?.status ?? 'Pending'}</Badge><Badge>{test.priority}</Badge><Badge>{test.category}</Badge>{result?.verification_path && <Badge>{result.verification_path}</Badge>}<span className={`confidence-bars level-${confidence.level}`}><i /><i /><i /></span><small>{confidence.label}</small></div></div>{open ? <ChevronUp size={18} /> : <ChevronDown size={18} />}</button>{open && <div className="test-card-details"><div><h3>Test steps</h3><ol>{test.steps.map((step, index) => <li key={`${test.id}-step-${index}`}>{step}</li>)}</ol></div><div><h3>Expected results</h3><ul>{test.expected_results.map((expected, index) => <li key={`${test.id}-expected-${index}`}>{expected}</li>)}</ul></div>{result && <div className="evidence-panel"><h3>Verification details</h3><p><strong>{result.verification_path ?? 'Rule-Based'}</strong> · {confidence.label}</p>{result.findings.map((finding) => <span key={finding.check} className={`finding-${finding.status.toLowerCase()}`}><CheckCircle2 size={14} /><span><strong>{finding.check.replaceAll('_', ' ')}</strong>{finding.detail}</span></span>)}<h3>Source evidence</h3>{result.evidence.length ? result.evidence.map((item, index) => <span key={`${item.file}-${item.line}-${index}`}><Code2 size={14} /><span><strong>{item.file}{item.line ? `:${item.line}` : ''}</strong>{item.detail}</span></span>) : <p>No direct source references were returned.</p>}</div>}</div>}</article> })}</div></section>)}{!filtered.length && <Empty title="No matching tests" detail="Adjust the category, priority, or verification filters." />}</div>
}

export function LegacyTestCasesPage() {
  const state = useAppState()
  const tests = state.artifacts.generation?.generated_test_cases ?? []
  const verification = state.artifacts.verification
  const project = state.projects.find((item) => item.id === state.activeProjectId)
  return <div className="page"><PageHeader title="Generate Tests" subtitle={project ? `Production-ready unit test suite for ${project.name}.` : 'Generate, verify, and export production-ready unit tests.'} action={tests.length ? <Button variant="secondary" onClick={() => download(`${project?.name ?? 'project'}-test-cases`, state.artifacts.generation)}><Download size={16} /> Export Test Suite</Button> : undefined} />
    <ActiveProjectGate>{state.artifactsLoading ? <ResultSkeleton /> : tests.length ? <><div className="metrics three"><MetricCard icon={TestTube2} title="Generated unit tests" value={tests.length} helper="Production-ready suite" /><MetricCard icon={ShieldCheck} title="AI verified" value={verification?.summary.verified ?? 0} helper="Confirmed against source behavior" /><MetricCard icon={Gauge} title="Quality score" value={state.artifacts.quality ? `${state.artifacts.quality.final_score}%` : '—'} helper="After automatic optimization" /></div><Section title="Production-ready test suite" description="Grouped by target with evidence and confidence at a glance."><TestCaseGroups tests={tests} /></Section></> : <Empty title="No unit tests generated yet" detail="Choose a backend project and generate its production-ready unit test suite." action={<Button onClick={() => state.openUpload('zip')}>Generate Unit Tests</Button>} />}</ActiveProjectGate>
  </div>
}

export function TestCasesPage() {
  const state = useAppState()
  const navigate = useNavigate()
  const tests = state.artifacts.generation?.generated_test_cases ?? []
  const verification = state.artifacts.verification
  const project = state.projects.find((item) => item.id === state.activeProjectId)
  const coverage = state.artifacts.quality?.quality_evaluation.dimension_scores.coverage ?? state.artifacts.generation?.coverage_summary.requirement_coverage ?? null
  return <div className="page generated-tests-page"><ActiveProjectGate>{state.artifactsLoading ? <ResultSkeleton /> : tests.length && project ? <TestExplorer tests={tests} verification={verification ?? null} runtime={null} coverage={typeof coverage === 'number' ? coverage : null} generationStatus={state.artifacts.generation?.generation_status} projectName={project.name} projectId={project.id} onOpenRuntime={() => navigate(`/runtime-validation/${project.id}`)} /> : <Empty title="No generated tests yet" detail="Choose a backend project and generate its unit test suite to open the Test Explorer." action={<Button onClick={() => state.openUpload('zip')}>Generate Unit Tests</Button>} />}</ActiveProjectGate></div>
}

export function LegacyReportsPage() {
  const state = useAppState()
  const navigate = useNavigate()
  const quality = state.artifacts.quality
  const verification = state.artifacts.verification
  const generation = state.artifacts.generation
  const understanding = state.artifacts.understanding?.result
  const security = state.artifacts.securityScan
  const project = state.projects.find((item) => item.id === state.activeProjectId)
  const coverage = quality?.quality_evaluation.dimension_scores.coverage ?? generation?.coverage_summary.requirement_coverage ?? 0
  const feedbackMissing = quality?.quality_evaluation.feedback.missing_categories
  const missingCoverage = Array.isArray(feedbackMissing) ? feedbackMissing.filter((item): item is string => typeof item === 'string') : []
  const recommendations = quality?.quality_evaluation.recommendations ?? []
  const riskCount = (understanding?.ambiguities?.length ?? 0) + (verification?.summary.failed ?? 0)
  const exports = [
    ['Security scan', 'security-scan', security],
    ['Generated test cases', 'test-cases', generation],
    ['Verification results', 'verification', verification],
    ['Coverage and quality', 'quality-report', quality],
  ] as const
  return <div className="page"><PageHeader title="Reports" subtitle={project ? `Quality and verification results for ${project.name}.` : 'Final coverage, quality, and export options.'} action={quality && state.activeProjectId ? <div className="header-actions"><RegenerateStage4Action projectId={state.activeProjectId} /><Button onClick={() => navigate(`/runtime-validation/${state.activeProjectId}`)}><ShieldCheck size={16} /> Runtime Validation</Button></div> : undefined} />
    <ActiveProjectGate>{state.artifactsLoading ? <ResultSkeleton /> : quality && verification && generation ? <>
      <section className="ai-summary"><div className="ai-summary-head"><span><BrainCircuit size={21} /></span><div><small>AI project brief</small><h2>{understanding?.project_summary || 'Project analysis complete'}</h2></div><Badge tone="success">Analysis complete</Badge></div><p>{understanding?.architecture || 'The project was analyzed and converted into an optimized, verified test suite.'}</p><div className="summary-insights"><span><Layers3 size={16} /><strong>{understanding?.components?.length ?? 0}</strong> modules analyzed</span><span><TestTube2 size={16} /><strong>{generation.total_after_deduplication}</strong> tests generated</span><span><Gauge size={16} /><strong>{quality.final_score}%</strong> quality</span><span><CircleAlert size={16} /><strong>{riskCount}</strong> risks to review</span></div></section>
      <div className="report-dashboard"><article className="score-card"><div className="score-ring" style={{ '--score': `${quality.final_score * 3.6}deg` } as CSSProperties}><div><strong>{quality.final_score}</strong><span>Quality</span></div></div><div><Badge tone={quality.quality_evaluation.threshold_met ? 'success' : 'warning'}>{quality.quality_evaluation.threshold_met ? 'Target met' : 'Review suggested'}</Badge><h3>Overall test quality</h3><p>Improved by {quality.improvement_metrics.score_delta.toFixed(1)} points across {quality.iterations} iteration{quality.iterations === 1 ? '' : 's'}.</p></div></article>
        <article className="coverage-card"><div className="card-icon"><Target size={20} /></div><span>Coverage</span><strong>{Math.round(coverage)}%</strong><div className="coverage-track"><i style={{ width: `${Math.min(100, coverage)}%` }} /></div><small>{missingCoverage.length ? `${missingCoverage.length} areas need attention` : 'No missing categories reported'}</small></article>
        <article className="report-number-card"><div className="card-icon success"><CheckCircle2 size={20} /></div><span>Verified tests</span><strong>{verification.summary.verified}</strong><small>{verification.summary.partial} partial · {verification.summary.failed} failed</small></article>
        <article className="report-number-card"><div className="card-icon"><TestTube2 size={20} /></div><span>Generated tests</span><strong>{generation.total_after_deduplication}</strong><small>{generation.total_generated - generation.total_after_deduplication} duplicates removed</small></article>
      </div>
      <div className="report-grid"><Section title="Quality dimensions" description="Final static-analysis scores after automatic regeneration. Runtime performance requires execution and is not scored here."><div className="dimension-list">{Object.entries(quality.quality_evaluation.dimension_scores).filter(([name]) => name !== 'performance').map(([name, value]) => <div key={name}><span>{name.replaceAll('_', ' ')}</span><strong>{value}%</strong><div><i style={{ width: `${value}%` }} /></div></div>)}</div></Section>
        <Section title="Security scan" description={`Semgrep JSON report across ${security?.summary?.files_scanned ?? 0} scanned files.`}><div className="insight-card-list">{security?.findings.length ? security.findings.slice(0, 20).map((finding) => <div key={finding.id}><CircleAlert size={17} /><div><strong>{finding.severity} · {finding.rule_id}</strong><small>{finding.file}:{finding.line} · {finding.message}</small>{(finding.cwe.length > 0 || finding.owasp.length > 0) && <small>{[...finding.cwe, ...finding.owasp].join(' · ')}</small>}</div></div>) : <div className="positive-insight"><ShieldCheck size={18} /><div><strong>No security findings</strong><small>Semgrep returned no findings for this scan.</small></div></div>}</div></Section>
        <Section title="Coverage gaps" description="Areas the AI recommends reviewing next."><div className="insight-card-list">{missingCoverage.length ? missingCoverage.map((item) => <div key={item}><CircleAlert size={17} /><div><strong>{item}</strong><small>Additional scenarios may improve coverage.</small></div></div>) : <div className="positive-insight"><CheckCircle2 size={18} /><div><strong>No missing categories reported</strong><small>The configured coverage target is represented.</small></div></div>}</div></Section></div>
      <div className="report-grid"><Section title="AI recommendations" description="Actionable guidance from the final evaluation."><div className="recommendation-list">{recommendations.length ? recommendations.map((recommendation, index) => <div key={`${recommendation}-${index}`}><span><Lightbulb size={16} /></span><p>{recommendation}</p></div>) : <div className="positive-insight"><CheckCircle2 size={18} /><div><strong>No additional recommendations</strong><small>The quality evaluator returned no outstanding actions.</small></div></div>}</div></Section>
        <Section title="Export workspace" description="Download final persisted artifacts as JSON."><div className="export-card-grid">{exports.map(([label, filename, data]) => <button key={label} onClick={() => download(`${project?.name ?? 'project'}-${filename}`, data)}><span><Download size={17} /></span><div><strong>{label}</strong><small>JSON export</small></div><ArrowRight size={16} /></button>)}</div></Section></div>
    </> : <Empty title="No report available" detail="A report appears when analysis and quality optimization complete." action={<Button onClick={() => navigate('/projects')}>Choose project</Button>} />}</ActiveProjectGate>
  </div>
}

export function ReportsPage() {
  return <div className="page executive-report-page"><ExecutiveReport /></div>
}

export function HistoryPage() {
  const state = useAppState()
  const navigate = useNavigate()
  const [query, setQuery] = useState('')
  const [status, setStatus] = useState('all')
  const [date, setDate] = useState('all')
  const [sort, setSort] = useState('recent')
  const [selectedId, setSelectedId] = useState('')
  const [historyNow] = useState(() => Date.now())
  const selected = state.projects.find((project) => project.id === selectedId)
  const projects = [...state.projects].filter((project) => {
    const age = historyNow - new Date(project.created_at).getTime()
    return project.name.toLowerCase().includes(query.toLowerCase()) && (status === 'all' || project.status === status) && (date === 'all' || date === 'today' && age < 86400000 || date === 'week' && age < 604800000 || date === 'month' && age < 2592000000)
  }).sort((left, right) => sort === 'name' ? left.name.localeCompare(right.name) : sort === 'status' ? left.status.localeCompare(right.status) : new Date(right.updated_at).getTime() - new Date(left.updated_at).getTime())
  const activeArtifacts = selected?.id === state.activeProjectId ? state.artifacts : undefined
  const activeJob = selected ? state.jobs[selected.id] : undefined
  const generation = activeArtifacts?.generation
  const quality = activeArtifacts?.quality
  const dependency = activeArtifacts?.dependency
  const language = dependency ? [...new Set(dependency.files.map((file) => file.language).filter(Boolean))].join(', ') : ''
  const openProject = (projectId: string) => { state.setActiveProjectId(projectId); setSelectedId(projectId) }
  const removeProject = async (projectId: string) => { if (!window.confirm('Delete this project and its saved artifacts?')) return; await api.deleteProject(projectId); state.removeProject(projectId); await state.refreshProjects() }

  if (selected) {
    const reportCandidates: Array<[string, string, unknown | undefined]> = [
      ['Security Report', 'security-report', activeArtifacts?.securityScan],
      ['Coverage Report', 'coverage-report', generation?.coverage_summary],
      ['Generated Tests', 'generated-tests', generation],
      ['Verification Report', 'verification-report', activeArtifacts?.verification],
      ['Quality Report', 'quality-report', quality],
      ['Execution Log', 'execution-log', activeJob?.logs],
    ]
    const reports = reportCandidates.filter((entry): entry is [string, string, unknown] => entry[2] != null)
    const stages = ['Uploaded', 'Security Scan', 'Target Discovery', 'Generation', 'Verification', 'Optimization', 'Runtime Validation']
    const currentStage = Number(activeJob?.currentStage?.slice(-1) ?? 1)
    return <div className="page history-details-page"><button className="history-back" onClick={() => setSelectedId('')}><ArrowRight size={14} /> Back to History</button><header className="history-details-head"><div><small>Project history</small><h1>{selected.name}</h1><p>{selected.source_type === 'GITHUB' ? 'GitHub Repository' : 'ZIP Archive'} · Created {new Date(selected.created_at).toLocaleString()}</p></div><Badge tone={tone(selected.status)}>{selected.status}</Badge></header>
      <section className="history-detail-summary"><article><span>Status</span><strong>{selected.status}</strong></article><article><span>Progress</span><strong>{activeJob?.progress ?? 0}%</strong></article>{generation && <article><span>Generated Tests</span><strong>{generation.total_after_deduplication}</strong></article>}{quality && <article><span>Quality Score</span><strong>{quality.final_score}%</strong></article>}{language && <article><span>Language</span><strong>{language}</strong></article>}</section>
      <div className="history-detail-grid"><section><h2>Project Information</h2><dl><div><dt>Project ID</dt><dd>{selected.id}</dd></div><div><dt>Repository type</dt><dd>{selected.source_type}</dd></div><div><dt>Created</dt><dd>{new Date(selected.created_at).toLocaleString()}</dd></div><div><dt>Last updated</dt><dd>{new Date(selected.updated_at).toLocaleString()}</dd></div>{dependency && <div><dt>Files analyzed</dt><dd>{dependency.files.length}</dd></div>}</dl></section><section><h2>Recent Activity</h2><div className="history-detail-activity">{activeJob?.timeline.slice().reverse().map((event) => <article key={event.id}><CheckCircle2 size={14} /><span><strong>{event.label}</strong><small>{event.at.toLocaleString()}</small></span></article>) ?? <p>No project activity is available.</p>}</div></section></div>
      <section className="history-pipeline"><h2>Pipeline Timeline</h2>{stages.map((stage, index) => { const number = index + 1; const complete = number < currentStage || activeJob?.status === 'complete'; const current = number === currentStage; return <article className={complete ? 'complete' : current ? activeJob?.status ?? 'current' : 'pending'} key={stage}><span>{complete ? <CheckCircle2 size={15} /> : current && activeJob?.status === 'failed' ? <CircleAlert size={15} /> : <Clock3 size={15} />}</span><div><strong>{stage}</strong><small>{complete ? 'Completed' : current ? activeJob?.status : 'Pending'}</small>{current && activeJob?.logs?.length ? <details><summary>View logs</summary><pre>{activeJob.logs.join('\n')}</pre></details> : null}</div></article> })}</section>
      <section className="history-reports"><h2>Available Reports</h2>{reports.length ? <div>{reports.map(([label, filename, value]) => <button key={label} onClick={() => download(`${selected.name}-${filename}`, value)}><Download size={17} /><span><strong>{label}</strong><small>Download JSON</small></span><ArrowRight size={14} /></button>)}</div> : <Empty title="No reports available" detail="Reports appear as the project workflow completes." />}</section>
    </div>
  }

  const completed = state.projects.filter((project) => project.status === 'READY').length
  const running = state.projects.filter((project) => project.status === 'PROCESSING').length
  const failed = state.projects.filter((project) => project.status === 'FAILED').length
  const generatedTotal = state.artifacts.generation?.total_after_deduplication
  const runtimeValidated = Object.values(state.jobs).filter((job) => job.currentStage === 'stage_7' && job.status === 'complete').length
  return <div className="page history-dashboard"><PageHeader title="History" subtitle="Browse previous projects, executions, generated tests, reports, and runtime validations." />
    <section className="history-toolbar"><label><Search size={15} /><input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Search projects" /></label><select value={status} onChange={(event) => setStatus(event.target.value)}><option value="all">All statuses</option><option value="READY">Completed</option><option value="PROCESSING">Running</option><option value="FAILED">Failed</option><option value="UPLOADED">Draft</option></select><select value={date} onChange={(event) => setDate(event.target.value)}><option value="all">Any date</option><option value="today">Today</option><option value="week">Last 7 days</option><option value="month">Last 30 days</option></select><select value={sort} onChange={(event) => setSort(event.target.value)}><option value="recent">Recent</option><option value="name">Name</option><option value="status">Status</option></select><Button onClick={() => state.openUpload('zip')}><Upload size={15} /> New Project</Button></section>
    <section className="history-stats"><article><span>Projects</span><strong>{state.projects.length}</strong></article><article><span>Completed</span><strong>{completed}</strong></article><article><span>Running</span><strong>{running}</strong></article><article><span>Failed</span><strong>{failed}</strong></article><article><span>Draft</span><strong>{state.projects.filter((project) => project.status === 'UPLOADED').length}</strong></article>{generatedTotal != null && <article><span>Generated Tests</span><strong>{generatedTotal}</strong></article>}<article><span>Runtime Validated</span><strong>{runtimeValidated}</strong></article></section>
    {state.activities.length > 0 && <section className="history-recent"><h2>Recent Activity</h2><div>{state.activities.slice(0, 8).map((activity) => <article key={activity.id}><HistoryIcon size={14} /><span><strong>{activity.label}</strong><small>{activity.detail}</small></span><time>{activity.at.toLocaleString()}</time></article>)}</div></section>}
    <section className="history-projects"><header><h2>Project History</h2><span>{projects.length} projects</span></header>{projects.length ? <div>{projects.map((project) => { const job = state.jobs[project.id]; const isActive = project.id === state.activeProjectId; const projectGeneration = isActive ? state.artifacts.generation : undefined; const projectDependency = isActive ? state.artifacts.dependency : undefined; const projectQuality = isActive ? state.artifacts.quality : undefined; return <article key={project.id} onClick={() => openProject(project.id)} tabIndex={0}><header><span>{project.source_type === 'GITHUB' ? <FolderGit2 size={18} /> : <FileArchive size={18} />}</span><div><h3>{project.name}</h3><p>{project.source_type === 'GITHUB' ? 'GitHub Repository' : 'ZIP Archive'} · Created {new Date(project.created_at).toLocaleString()}</p></div><Badge tone={tone(project.status)}>{project.status}</Badge></header><div className="history-card-metrics"><span>Progress<strong>{job?.progress ?? 0}%</strong></span>{projectDependency && <><span>Language<strong>{[...new Set(projectDependency.files.map((file) => file.language).filter(Boolean))].join(', ')}</strong></span><span>Files<strong>{projectDependency.files.length}</strong></span></>}{projectGeneration && <span>Generated Tests<strong>{projectGeneration.total_after_deduplication}</strong></span>}{job?.currentStage === 'stage_7' && <span>Runtime Validation<strong>{job.status === 'complete' ? 'Completed' : job.status}</strong></span>}{projectQuality && <span>Quality Score<strong>{projectQuality.final_score}%</strong></span>}</div><footer><Button variant="secondary" onClick={(event) => { event.stopPropagation(); state.setActiveProjectId(project.id); navigate(`/processing/${project.id}`) }}>{job?.status === 'failed' || job?.status === 'paused' ? 'Resume' : 'Open'}</Button><Button variant="secondary" onClick={(event) => { event.stopPropagation(); state.setActiveProjectId(project.id); navigate('/reports') }}>Reports</Button><Button variant="ghost" onClick={(event) => { event.stopPropagation(); void removeProject(project.id) }}><Trash2 size={14} /> Delete</Button><button className="history-open" onClick={(event) => { event.stopPropagation(); openProject(project.id) }}>Open <ArrowRight size={14} /></button></footer></article> })}</div> : <Empty title="No matching projects" detail="Adjust the search or filters, or create a new project." />}</section>
  </div>
}

export function SettingsPage() {
  const [status, setStatus] = useState('Checking…')
  useEffect(() => { api.health().then(() => setStatus('Healthy')).catch(() => setStatus('Unavailable')) }, [])
  return <div className="page narrow"><PageHeader title="Settings" subtitle="Interface preferences and service availability." /><Section title="API status"><div className="settings-row"><div><strong>Backend service</strong><small>Connection to the TestForge API</small></div><Badge tone={status === 'Healthy' ? 'success' : 'danger'}>{status}</Badge></div></Section><Section title="About"><div className="settings-row"><div><strong>Automatic quality optimization</strong><small>Test suites are regenerated until the configured server threshold is met.</small></div><BarChart3 size={20} /></div></Section></div>
}
