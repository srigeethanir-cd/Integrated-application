import { useEffect, useMemo, useState, type ReactNode } from 'react'
import { Check, ChevronDown, ChevronRight, Clipboard, Download, FileCode2, Folder, PanelLeftClose, PanelLeftOpen, Search } from 'lucide-react'
import type { RuntimeValidationReport, TestCase, VerificationResult } from '../api/types'
import { api } from '../api/client'
import { Badge, Button } from './ui'

interface TestExplorerProps {
  tests: TestCase[]
  verification: VerificationResult | null
  runtime: RuntimeValidationReport | null
  coverage: number | null
  generationStatus?: string
  generationTimestamp?: Date | null
  projectName: string
  projectId?: string
  onOpenRuntime: () => void
}

const relative = (value?: unknown) => String(value ?? '').replaceAll('\\', '/')
const symbol = (test: TestCase) => String(test.unit_test?.symbol ?? test.traceability?.symbol ?? test.traceability?.target ?? '')
const sourceFile = (test?: TestCase) => relative(test?.unit_test?.file ?? test?.traceability?.file ?? test?.traceability?.source_file)
const verificationFor = (test: TestCase, verification: VerificationResult | null) => verification?.results.find((item) => item.test_case_id === test.id)
const runtimeFor = (test: TestCase, runtime: RuntimeValidationReport | null) => runtime?.results.find((item) => item.test_case_id === test.id)

function highlightedLine(line: string): ReactNode[] {
  const pattern = /(#.*$|"(?:\\.|[^"\\])*"|'(?:\\.|[^'\\])*'|\b(?:async|await|def|class|return|raise|with|as|if|elif|else|for|in|from|import|assert|try|except|True|False|None)\b|@[A-Za-z_][\w.]*)/g
  return line.split(pattern).filter(Boolean).map((part, index) => {
    const kind = part.startsWith('#') ? 'comment' : part.startsWith('"') || part.startsWith("'") ? 'string' : part.startsWith('@') ? 'decorator' : /^(async|await|def|class|return|raise|with|as|if|elif|else|for|in|from|import|assert|try|except|True|False|None)$/.test(part) ? 'keyword' : ''
    return kind ? <span className={`syntax-${kind}`} key={index}>{part}</span> : <span key={index}>{part}</span>
  })
}

function downloadText(name: string, content: string) {
  const blob = new Blob([content], { type: 'text/x-python;charset=utf-8' })
  const href = URL.createObjectURL(blob)
  const anchor = document.createElement('a')
  anchor.href = href
  anchor.download = name.endsWith('.py') ? name : `${name}.py`
  anchor.click()
  URL.revokeObjectURL(href)
}

function aggregateVerification(verification: VerificationResult | null) {
  if (!verification) return null
  if (verification.summary.failed) return { label: `${verification.summary.failed} failed`, tone: 'danger' as const }
  if (verification.summary.partial) return { label: `${verification.summary.partial} need review`, tone: 'warning' as const }
  return { label: 'Verified', tone: 'success' as const }
}

export function TestExplorer({ tests, verification, runtime, projectName, projectId }: TestExplorerProps) {
  const [query, setQuery] = useState('')
  const [selectedId, setSelectedId] = useState(tests[0]?.id ?? '')
  const [treeOpen, setTreeOpen] = useState(true)
  const [copied, setCopied] = useState(false)
  const [exporting, setExporting] = useState(false)
  const [exportError, setExportError] = useState('')

  const filtered = useMemo(() => tests.filter((test) => [test.title, test.id, test.category, sourceFile(test), symbol(test)].join(' ').toLowerCase().includes(query.toLowerCase())), [query, tests])
  const groups = useMemo(() => Object.entries(filtered.reduce<Record<string, TestCase[]>>((result, test) => {
    const file = sourceFile(test) || 'Generated tests'
    return { ...result, [file]: [...(result[file] ?? []), test] }
  }, {})).sort(([left], [right]) => left.localeCompare(right)), [filtered])
  const selected = tests.find((test) => test.id === selectedId) ?? filtered[0] ?? tests[0]
  const code = selected?.unit_test?.generated_code ?? ''
  const target = selected ? symbol(selected) : ''
  const targetFunction = target.split('.').filter(Boolean).at(-1) ?? ''
  const selectedVerification = selected ? verificationFor(selected, verification) : undefined
  const selectedRuntime = selected ? runtimeFor(selected, runtime) : undefined
  const fixtures = selected?.unit_test?.fixture_names ?? []
  const patches = selected?.unit_test?.patches ?? []
  const assertions = selected?.expected_results ?? []
  const verificationStatus = aggregateVerification(verification)
  const runtimeStatus = runtime ? { label: `${runtime.pass_rate}% passed`, tone: runtime.summary.failed ? 'danger' as const : 'success' as const } : null
  const exportSuite = async () => {
    if (!projectId) return
    setExporting(true)
    setExportError('')
    try {
      const blob = await api.exportTestSuite(projectId)
      const href = URL.createObjectURL(blob)
      const anchor = document.createElement('a')
      anchor.href = href
      anchor.download = 'test-suite.zip'
      anchor.click()
      URL.revokeObjectURL(href)
    } catch (reason) {
      setExportError(reason instanceof Error ? reason.message : 'Unable to export the test suite')
    } finally {
      setExporting(false)
    }
  }

  useEffect(() => {
    if (selected && filtered.includes(selected)) return
    setSelectedId(filtered[0]?.id ?? '')
  }, [filtered, selected])

  if (!tests.length) return <div className="test-explorer-empty"><FileCode2 size={24} /><strong>No generated tests yet.</strong><span>Generated pytest files will appear here when they are available.</span></div>

  return <section className={`test-explorer ide-test-explorer ${treeOpen ? '' : 'tree-collapsed'}`}>
    <header className="ide-test-header">
      <div className="ide-test-project"><strong>{projectName}</strong><span>{tests.length} generated test{tests.length === 1 ? '' : 's'}</span>{verificationStatus && <Badge tone={verificationStatus.tone}>{verificationStatus.label}</Badge>}{runtimeStatus && <Badge tone={runtimeStatus.tone}>{runtimeStatus.label}</Badge>}</div>
      <label className="ide-test-search"><Search size={15} aria-hidden="true" /><span className="sr-only">Search generated tests</span><input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Search tests" /></label>
      {projectId && <Button loading={exporting} onClick={() => void exportSuite()}><Download size={15} /> Export</Button>}
      {exportError && <span className="ide-export-error" role="alert" title={exportError}>{exportError}</span>}
    </header>

    <div className="ide-test-layout">
      <aside className="ide-test-tree" aria-label="Generated test explorer">
        <header><button aria-label="Collapse test explorer" onClick={() => setTreeOpen(false)}><PanelLeftClose size={15} /></button><strong>Tests</strong><span>{filtered.length}</span></header>
        <div className="ide-test-tree-scroll">{groups.length ? groups.map(([file, fileTests]) => <details open key={file}><summary><ChevronDown size={13} /><Folder size={14} /><span title={file}>{file}</span><small>{fileTests.length}</small></summary>{fileTests.map((test) => <button className={selected?.id === test.id ? 'selected' : ''} key={test.id} onClick={() => setSelectedId(test.id)}><FileCode2 size={14} /><span>{test.title}</span>{verificationFor(test, verification)?.status === 'Verified' && <Check size={13} />}</button>)}</details>) : <p>No tests match your search.</p>}</div>
      </aside>

      {!treeOpen && <button className="ide-tree-restore" aria-label="Open test explorer" onClick={() => setTreeOpen(true)}><PanelLeftOpen size={16} /></button>}

      <main className="ide-code-workspace">
        <header className="ide-editor-header"><div><FileCode2 size={14} /><span>{selected?.title}</span>{sourceFile(selected) && <small>{sourceFile(selected)}</small>}</div><div><Button variant="ghost" onClick={async () => { await navigator.clipboard.writeText(code); setCopied(true); window.setTimeout(() => setCopied(false), 1500) }}><Clipboard size={14} /> {copied ? 'Copied' : 'Copy'}</Button><Button variant="ghost" onClick={() => downloadText(`test_${targetFunction || selected?.id}.py`, code)}><Download size={14} /> Download</Button></div></header>
        <div className="ide-code-editor" tabIndex={0} aria-label={`Read-only generated code for ${selected?.title}`}><ol>{code.split('\n').map((line, index) => <li key={index}><code>{highlightedLine(line) || ' '}</code></li>)}</ol></div>
        <details className="ide-test-details"><summary><span><ChevronRight size={14} /> Test details</span><small>{selectedVerification?.status ?? selectedRuntime?.runtime_status ?? selected?.category}</small></summary><dl>
          {sourceFile(selected) && <div><dt>Target file</dt><dd>{sourceFile(selected)}</dd></div>}
          {targetFunction && <div><dt>Target function</dt><dd>{targetFunction}</dd></div>}
          {selected?.category && <div><dt>Test category</dt><dd>{selected.category}</dd></div>}
          {patches.length > 0 && <div><dt>Mocks used</dt><dd>{patches.join(', ')}</dd></div>}
          {fixtures.length > 0 && <div><dt>Fixtures</dt><dd>{fixtures.join(', ')}</dd></div>}
          {assertions.length > 0 && <div><dt>Assertions</dt><dd>{assertions.join('; ')}</dd></div>}
          {selectedRuntime && <div><dt>Runtime status</dt><dd>{selectedRuntime.runtime_status}</dd></div>}
          {selected?.description && <div className="wide"><dt>AI explanation</dt><dd>{selected.description}</dd></div>}
        </dl></details>
      </main>
    </div>
  </section>
}
