import { useMemo, useState } from 'react'
import { ArrowRight, CheckCircle2, FileCode2, Search, ShieldCheck } from 'lucide-react'
import type { DependencyRun, Project, SecurityFinding, SecurityScan } from '../api/types'
import { Badge, Button, Empty } from './ui'

interface SecurityReviewProps {
  project: Project
  scan: SecurityScan
  dependency?: DependencyRun
  onContinue: () => void
}

const severity = (finding: SecurityFinding) => finding.severity.toUpperCase()
const severityTone = (value: string) => /CRITICAL|HIGH|ERROR/.test(value) ? 'danger' as const : /MEDIUM|WARNING/.test(value) ? 'warning' as const : 'info' as const
const relativePath = (value: string) => value.replaceAll('\\', '/').replace(/^.*\/(source|workspace)\//i, '')
const metadataText = (finding: SecurityFinding, ...keys: string[]) => {
  for (const key of keys) {
    const value = finding.metadata?.[key]
    if (typeof value === 'string' && value.trim()) return value
    if (Array.isArray(value) && value.every((item) => typeof item === 'string')) return value.join('\n')
  }
  return null
}

export function SecurityReview({ project, scan, dependency, onContinue }: SecurityReviewProps) {
  const [query, setQuery] = useState('')
  const findings = scan.findings
  const counts = {
    critical: findings.filter((item) => severity(item) === 'CRITICAL').length,
    high: findings.filter((item) => ['HIGH', 'ERROR'].includes(severity(item))).length,
    medium: findings.filter((item) => ['MEDIUM', 'WARNING'].includes(severity(item))).length,
    low: findings.filter((item) => ['LOW', 'INFO', 'INFORMATIONAL'].includes(severity(item))).length,
  }
  const score = scan.summary?.security_score ?? Math.max(0, 100 - counts.critical * 25 - counts.high * 15 - counts.medium * 7 - counts.low * 2)
  const filtered = useMemo(() => findings.filter((finding) => [finding.rule_id, finding.file, finding.message, finding.recommendation, finding.severity].join(' ').toLowerCase().includes(query.toLowerCase())), [findings, query])
  const framework = dependency?.analysis?.framework ?? dependency?.analysis?.detected_framework
  const duration = scan.summary?.duration_ms == null ? null : scan.summary.duration_ms < 1000 ? `${scan.summary.duration_ms} ms` : `${(scan.summary.duration_ms / 1000).toFixed(1)} s`

  return <main className="security-review-page">
    <header className="security-review-header"><div><span><ShieldCheck size={16} /> Security Review</span><h1>{project.name}</h1><p>Review the Semgrep findings before TestForge generates and validates the unit test suite.</p></div><div className="security-score"><small>Security score</small><strong>{score}</strong><span>/ 100</span></div></header>

    <section className="security-overview" aria-label="Security scan overview">
      <div><small>Critical</small><strong className="critical">{counts.critical}</strong></div><div><small>High</small><strong className="high">{counts.high}</strong></div><div><small>Medium</small><strong className="medium">{counts.medium}</strong></div><div><small>Low</small><strong>{counts.low}</strong></div>
      {scan.summary && <div><small>Files scanned</small><strong>{scan.summary.files_scanned}</strong></div>}
      {duration && <div><small>Scan duration</small><strong>{duration}</strong></div>}
    </section>

    <section className="security-repository-summary"><div><FileCode2 size={18} /><span><small>Repository</small><strong>{project.name}</strong></span></div>{dependency?.files.length ? <div><small>Source files</small><strong>{dependency.files.length}</strong></div> : null}{typeof framework === 'string' && framework ? <div><small>Framework</small><strong>{framework}</strong></div> : null}<div><small>Scan engine</small><strong>{scan.summary?.engine ?? 'Semgrep'}</strong></div><div><small>Findings</small><strong>{findings.length}</strong></div></section>

    <section className="security-findings-panel"><header><div><h2>Vulnerabilities</h2><p>{filtered.length} of {findings.length} findings</p></div><label><Search size={15} /><span className="sr-only">Search vulnerabilities</span><input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Search rule, file, or description" /></label></header>
      {filtered.length ? <div className="security-finding-table"><div className="security-finding-columns"><span>Severity</span><span>Issue</span><span>Location</span><span>Rule</span></div>{filtered.map((finding) => { const snippet = finding.code_snippet || metadataText(finding, 'code', 'snippet', 'lines', 'source'); return <details key={finding.id}><summary><Badge tone={severityTone(finding.severity)}>{finding.severity}</Badge><span><strong>{finding.message}</strong><small>{finding.category || finding.recommendation || finding.rule_id}{finding.duplicate_count > 1 ? ` · ${finding.duplicate_count} identical results grouped` : ''}</small></span><span><strong>{relativePath(finding.file)}</strong><small>Lines {finding.start_line}–{finding.end_line}</small></span><code>{finding.rule_id}</code></summary><div className="security-finding-detail"><section><h3>Description</h3><p>{finding.message}</p></section>{finding.recommendation && <section><h3>Recommended fix</h3><p>{finding.recommendation}</p></section>}<section><h3>Security metadata</h3><p>{[finding.category && `Category: ${finding.category}`, finding.confidence && `Confidence: ${finding.confidence}`, ...finding.cwe, ...finding.owasp].filter(Boolean).join(' · ') || 'No additional metadata was provided by Semgrep.'}</p></section>{snippet && <section className="wide"><h3>Code snippet</h3><pre>{snippet}</pre></section>}{finding.references.length > 0 && <section className="wide"><h3>References</h3><div className="security-reference-list">{finding.references.map((reference) => <a key={reference} href={reference} target="_blank" rel="noreferrer">{reference}</a>)}</div></section>}</div></details> })}</div> : <Empty title={findings.length ? 'No matching vulnerabilities' : 'No vulnerabilities detected'} detail={findings.length ? 'Try a different rule, file, severity, or description.' : 'Semgrep completed without persisted security findings.'} />}
    </section>

    <footer className="security-review-actions"><div><CheckCircle2 size={18} /><span><strong>Security analysis complete</strong><small>Generation will continue automatically after this checkpoint.</small></span></div><Button onClick={onContinue}>Continue Generation <ArrowRight size={16} /></Button></footer>
  </main>
}
