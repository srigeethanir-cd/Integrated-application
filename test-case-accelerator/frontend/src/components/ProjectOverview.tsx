import { useMemo, useState } from 'react'
import { AlertTriangle, Box, Braces, CheckCircle2, ChevronDown, Database, File, FileCode2, Folder, GitBranch, Globe2, KeyRound, Layers3, MessageSquare, Package, Play, Search, Server, Settings2, ShieldCheck, Trash2, X } from 'lucide-react'
import { useNavigate } from 'react-router-dom'
import { api } from '../api/client'
import type { FileMetadata, Project } from '../api/types'
import { Badge, Button, Empty, ErrorNotice, Loading } from './ui'
import { useAppState } from '../state/app-state'

type TreeNode = { name: string; path: string; children: Map<string, TreeNode>; file?: FileMetadata }

const unavailable = 'Not available'
const text = (value: unknown) => typeof value === 'string' && value.trim() ? value : unavailable
const values = (value: unknown) => Array.isArray(value) ? value.filter((item): item is string => typeof item === 'string' && Boolean(item.trim())) : []
const pathName = (value: string) => value.replaceAll('\\', '/').replace(/^.*\/(?:storage|uploads|workspace)\//i, '')

function metadataValue(metadata: Record<string, unknown> | null | undefined, ...keys: string[]) {
  for (const key of keys) if (metadata?.[key] != null) return metadata[key]
  return undefined
}

function buildTree(files: FileMetadata[]) {
  const root: TreeNode = { name: 'repository', path: '', children: new Map() }
  for (const file of files) {
    const normalized = pathName(file.path)
    let cursor = root
    normalized.split('/').filter(Boolean).forEach((part, index, parts) => {
      const path = parts.slice(0, index + 1).join('/')
      if (!cursor.children.has(part)) cursor.children.set(part, { name: part, path, children: new Map() })
      cursor = cursor.children.get(part)!
      if (index === parts.length - 1) cursor.file = file
    })
  }
  return root
}

function TreeBranch({ node, query, expandAll }: { node: TreeNode; query: string; expandAll: boolean }) {
  const children = [...node.children.values()].filter((child) => {
    if (!query) return true
    const matches = child.path.toLowerCase().includes(query.toLowerCase())
    const descendant = [...child.children.values()].some((nested) => nested.path.toLowerCase().includes(query.toLowerCase()))
    return matches || descendant
  }).sort((left, right) => Number(Boolean(left.file)) - Number(Boolean(right.file)) || left.name.localeCompare(right.name))
  return <>{children.map((child) => child.file ? <div className="repository-file" key={child.path}><File size={13} /><span>{child.name}</span><small>{child.file.language || unavailable}</small></div> : <TreeDirectory node={child} query={query} expandAll={expandAll} key={`${child.path}-${expandAll}-${Boolean(query)}`} />)}</>
}

function TreeDirectory({ node, query, expandAll }: { node: TreeNode; query: string; expandAll: boolean }) {
  const [open, setOpen] = useState(expandAll || Boolean(query))
  return <details open={open} onToggle={(event) => setOpen(event.currentTarget.open)}><summary><ChevronDown size={12} /><Folder size={14} /><span>{node.name}</span></summary><div><TreeBranch node={node} query={query} expandAll={expandAll} /></div></details>
}

function dependencyKind(name: string) {
  const value = name.toLowerCase()
  if (/sqlalchemy|postgres|mysql|sqlite|mongo|database|alembic/.test(value)) return 'Database'
  if (/redis|memcache|cache/.test(value)) return 'Cache'
  if (/jwt|jose|oauth|passlib|auth/.test(value)) return 'Authentication'
  if (/axios|requests|httpx|aiohttp|fetch/.test(value)) return 'HTTP Clients'
  if (/s3|boto|storage|azure-storage|gcs/.test(value)) return 'Storage'
  if (/kafka|rabbit|celery|pika|nats|message/.test(value)) return 'Messaging'
  return 'External Libraries'
}

export function ProjectOverview({ project }: { project: Project }) {
  const state = useAppState()
  const navigate = useNavigate()
  const [treeQuery, setTreeQuery] = useState('')
  const [expandAll, setExpandAll] = useState(true)
  const [deleteOpen, setDeleteOpen] = useState(false)
  const [deleting, setDeleting] = useState(false)
  const [deleteError, setDeleteError] = useState('')
  const dependency = state.artifacts.dependency
  const stage3 = state.artifacts.understanding?.result
  const security = state.artifacts.securityScan
  const files = dependency?.files ?? []
  const analysis = dependency?.analysis ?? {}
  const metadata = project.ingestion_metadata
  const tree = useMemo(() => buildTree(files), [files])
  const fileLanguages = [...new Set(files.map((file) => file.language).filter(Boolean))]
  const framework = metadataValue(analysis, 'framework', 'detected_framework') ?? metadataValue(metadata, 'framework')
  const language = metadataValue(analysis, 'language', 'primary_language') ?? metadataValue(metadata, 'language', 'primary_language') ?? fileLanguages.join(', ')
  const architecture = stage3?.architecture ?? metadataValue(analysis, 'architecture_style', 'architecture') ?? metadataValue(metadata, 'repository_type', 'project_type')
  const entryPoints = files.filter((file) => file.is_entry_point)
  const directories = new Set(files.flatMap((file) => { const parts = pathName(file.path).split('/'); return parts.slice(0, -1).map((_, index) => parts.slice(0, index + 1).join('/')) }))
  const functions = stage3?.functions?.length ?? files.reduce((total, file) => total + file.functions.length, 0)
  const classes = stage3?.classes?.length ?? files.reduce((total, file) => total + file.classes.length, 0)
  const modules = stage3?.modules?.length ?? files.length
  const groupedDependencies = analysis.dependency_groups as Record<string, unknown> | undefined
  const discoveredDependencies = [...new Set([
    ...values(analysis.dependencies),
    ...Object.values(groupedDependencies ?? {}).flatMap(values),
    ...(stage3?.external_dependencies ?? []),
  ])].sort()
  const dependencyGroups = discoveredDependencies.reduce<Record<string, string[]>>((groups, item) => {
    const kind = dependencyKind(item)
    return { ...groups, [kind]: [...(groups[kind] ?? []), item] }
  }, {})
  const components = stage3?.components ?? []
  const named = (pattern: RegExp) => components.filter((item) => pattern.test(`${item.name ?? ''} ${item.responsibility ?? ''} ${values(item.files).join(' ')}`))
  const repositories = [...named(/repository|data access|persistence/i), ...(stage3?.classes ?? []).filter((item) => /repository|repo/i.test(String(item.name ?? '')))]
  const utilities = [...named(/util|helper/i), ...(stage3?.functions ?? []).filter((item) => /util|helper/i.test(`${item.file ?? ''} ${item.name ?? ''}`))]
  const configFiles = files.filter((file) => /(^|\/)(pyproject\.toml|requirements[^/]*\.txt|package\.json|[^/]+\.(ya?ml|ini|cfg|toml|env))$/i.test(pathName(file.path)))
  const missing = [!language && 'Primary language', !framework && 'Framework', !entryPoints.length && 'Entry point', !stage3?.test_targets?.length && 'Executable test targets'].filter((item): item is string => Boolean(item))
  const warnings = [
    ...(stage3?.ambiguities ?? []).map((item) => String(item.description ?? item.reason ?? '')).filter(Boolean),
    ...(security?.summary?.diagnostics ?? []).filter((item) => /warning|error/i.test(item.level)).map((item) => item.message),
  ]
  const ready = Boolean(dependency && stage3 && stage3.test_targets.length && !state.artifacts.understanding?.failed_stage)

  const remove = async () => {
    setDeleting(true); setDeleteError('')
    try { await api.deleteProject(project.id); state.removeProject(project.id); await state.refreshProjects(); navigate('/projects') }
    catch (reason) { setDeleteError(reason instanceof Error ? reason.message : 'Project could not be deleted.') }
    finally { setDeleting(false) }
  }

  if (state.artifactsLoading) return <Loading label="Loading repository overview…" />
  return <div className="project-overview">
    <header className="project-overview-hero"><div><span>{project.source_type === 'GITHUB' ? <GitBranch /> : <Box />}</span><div><small>Project Overview</small><h1>{project.name}</h1><p>{stage3?.project_summary || project.description || 'Repository summary is not available.'}</p></div></div><Badge tone={project.status === 'FAILED' ? 'danger' : project.status === 'READY' ? 'success' : 'info'}>{project.status}</Badge></header>

    <section className="overview-section"><header><h2>Project Summary</h2><p>Repository identity and detected technology.</p></header><dl className="overview-facts"><div><dt>Project Name</dt><dd>{project.name}</dd></div><div><dt>Project Type</dt><dd>{text(architecture)}</dd></div><div><dt>Language</dt><dd>{text(language)}</dd></div><div><dt>Framework</dt><dd>{text(framework)}</dd></div><div><dt>Repository Source</dt><dd>{project.source_type === 'GITHUB' ? project.github_url || 'GitHub' : 'ZIP upload'}</dd></div><div><dt>Created Date</dt><dd>{new Date(project.created_at).toLocaleString()}</dd></div><div><dt>Current Status</dt><dd>{project.status}</dd></div></dl></section>

    <section className="overview-section"><header><h2>Repository Statistics</h2><p>Counts derived from discovered repository files and analysis.</p></header><div className="repository-stats"><span>Files<strong>{files.length || metadataValue(metadata, 'total_files', 'file_count')?.toString() || unavailable}</strong></span><span>Directories<strong>{directories.size || unavailable}</strong></span><span>Functions<strong>{functions || unavailable}</strong></span><span>Classes<strong>{classes || unavailable}</strong></span><span>Modules<strong>{modules || unavailable}</strong></span><span>Dependencies<strong>{discoveredDependencies.length || unavailable}</strong></span><span>Entry Points<strong>{entryPoints.length || unavailable}</strong></span></div></section>

    <div className="overview-two-column"><section className="overview-section repository-tree-panel"><header><div><h2>Repository Structure</h2><p>Project-relative discovered files.</p></div><div><label><Search size={14} /><input value={treeQuery} onChange={(event) => setTreeQuery(event.target.value)} placeholder="Search repository" /></label><Button variant="secondary" onClick={() => setExpandAll((value) => !value)}>{expandAll ? 'Collapse' : 'Expand'}</Button></div></header><div className="repository-tree"><TreeBranch node={tree} query={treeQuery} expandAll={expandAll} />{!files.length && <Empty title="Repository structure unavailable" detail="No discovered files were returned by dependency analysis." />}</div></section>
      <section className="overview-section repository-analysis"><header><h2>Repository Analysis</h2><p>Detected application structure.</p></header><div><article><Braces /><span>Detected Framework<strong>{text(framework)}</strong></span></article><article><Globe2 /><span>API Endpoints<strong>{stage3?.api_endpoints?.length ?? unavailable}</strong></span></article><article><Layers3 /><span>Business Services<strong>{named(/service|business/i).length || unavailable}</strong></span></article><article><Database /><span>Repositories<strong>{repositories.length || unavailable}</strong></span></article><article><Settings2 /><span>Utilities<strong>{utilities.length || unavailable}</strong></span></article><article><Box /><span>Models<strong>{stage3?.data_models?.length || unavailable}</strong></span></article><article><FileCode2 /><span>Configuration<strong>{configFiles.length || unavailable}</strong></span></article></div></section></div>

    <section className="overview-section"><header><h2>Dependency Summary</h2><p>External packages grouped by their detected role.</p></header><div className="dependency-overview">{['External Libraries', 'Database', 'Cache', 'Authentication', 'HTTP Clients', 'Storage', 'Messaging'].map((kind) => <article key={kind}>{kind === 'Database' ? <Database /> : kind === 'Authentication' ? <KeyRound /> : kind === 'HTTP Clients' ? <Globe2 /> : kind === 'Messaging' ? <MessageSquare /> : kind === 'Storage' ? <Server /> : <Package />}<div><strong>{kind}</strong>{dependencyGroups[kind]?.length ? <ul>{dependencyGroups[kind].map((item) => <li key={item}>{item}</li>)}</ul> : <small>Not detected</small>}</div></article>)}</div></section>

    <section className="overview-section readiness-panel"><header><h2>Test Generation Readiness</h2><Badge tone={ready ? 'success' : 'warning'}>{ready ? 'Ready for Test Generation' : 'Needs review'}</Badge></header><div><article><CheckCircle2 /><span>Readiness<strong>{ready ? 'Ready for Test Generation' : 'Analysis incomplete'}</strong></span></article><article><AlertTriangle /><span>Missing Information<strong>{missing.length ? missing.join(', ') : 'None reported'}</strong></span></article><article><ShieldCheck /><span>Warnings<strong>{warnings.length || 'None reported'}</strong></span></article><article><File /><span>Skipped Files<strong>{security?.summary?.skipped_files ?? unavailable}</strong></span></article><article><File /><span>Unsupported Files<strong>{security?.summary?.unsupported_files ?? unavailable}</strong></span></article></div>{warnings.length > 0 && <details><summary>Review warnings</summary><ul>{warnings.map((warning, index) => <li key={`${warning}-${index}`}>{warning}</li>)}</ul></details>}</section>

    <footer className="project-quick-actions"><div><strong>Continue with {project.name}</strong><small>Use the existing saved workflow and artifacts.</small></div><div><Button onClick={() => navigate(`/processing/${project.id}`)}><Play size={15} /> Generate Unit Tests</Button><Button variant="secondary" onClick={() => navigate(`/runtime-validation/${project.id}`)}>Open Runtime Validation</Button><Button variant="secondary" onClick={() => navigate('/reports')}>View Reports</Button><Button variant="secondary" onClick={() => setDeleteOpen(true)}><Trash2 size={15} /> Delete Project</Button></div></footer>

    {deleteOpen && <div className="dialog-backdrop"><div className="confirm-dialog" role="alertdialog" aria-modal="true" aria-labelledby="overview-delete-title"><button className="dialog-close" aria-label="Close" onClick={() => setDeleteOpen(false)}><X size={17} /></button><Trash2 className="dialog-danger" /><h2 id="overview-delete-title">Delete {project.name}?</h2><p>This permanently removes the project and its saved analysis.</p>{deleteError && <ErrorNotice message={deleteError} />}<div className="dialog-actions"><Button variant="secondary" disabled={deleting} onClick={() => setDeleteOpen(false)}>Cancel</Button><Button disabled={deleting} onClick={() => void remove()}>{deleting ? 'Deleting…' : 'Delete Project'}</Button></div></div></div>}
  </div>
}
