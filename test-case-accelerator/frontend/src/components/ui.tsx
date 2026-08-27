import { AlertCircle, LoaderCircle, type LucideIcon } from 'lucide-react'
import type { ButtonHTMLAttributes, ReactNode } from 'react'

export function Button({ variant = 'primary', className = '', loading = false, children, disabled, ...props }: ButtonHTMLAttributes<HTMLButtonElement> & { variant?: 'primary' | 'secondary' | 'ghost' | 'danger' | 'icon'; loading?: boolean }) {
  return <button className={`button button-${variant} ${className}`} aria-busy={loading || undefined} disabled={disabled || loading} {...props}>{loading && <LoaderCircle className="spin" size={16} aria-hidden="true" />}{children}</button>
}
export function PageHeader({ title, subtitle, action }: { title: string; subtitle: string; action?: ReactNode }) {
  return <div className="page-header"><div><h1>{title}</h1><p>{subtitle}</p></div>{action}</div>
}
export function MetricCard({ icon: Icon, title, value, helper }: { icon: LucideIcon; title: string; value: ReactNode; helper: string }) {
  return <article className="metric-card"><span className="icon-box"><Icon size={18} aria-hidden="true" /></span><span className="metric-title">{title}</span><strong>{value}</strong><small>{helper}</small></article>
}
export function Badge({ children, tone = 'neutral' }: { children: ReactNode; tone?: 'success' | 'info' | 'warning' | 'danger' | 'neutral' }) {
  return <span className={`badge badge-${tone}`} role="status">{children}</span>
}
export function Progress({ value, label }: { value: number; label?: string }) {
  const normalized = Math.min(100, Math.max(0, value))
  return <div className="progress" aria-label={label} role="progressbar" aria-valuemin={0} aria-valuemax={100} aria-valuenow={normalized}>{label && <div className="progress-label"><span>{label}</span><strong>{normalized}%</strong></div>}<div className="progress-track"><i style={{ width: `${normalized}%` }} /></div></div>
}
export function Skeleton({ lines = 3, label = 'Loading content' }: { lines?: number; label?: string }) {
  return <div className="skeleton" role="status" aria-label={label}>{Array.from({ length: lines }, (_, index) => <i key={index} />)}<span className="sr-only">{label}</span></div>
}
export function Loading({ label = 'Loading…' }: { label?: string }) { return <div className="state state-loading" role="status" aria-live="polite"><LoaderCircle className="spin" size={20} aria-hidden="true" /><p>{label}</p></div> }
export function Empty({ title, detail, action }: { title: string; detail: string; action?: ReactNode }) { return <div className="state"><h3>{title}</h3><p>{detail}</p>{action}</div> }
export function ErrorNotice({ message, action }: { message: string; action?: ReactNode }) { return <div className="error-notice" role="alert"><AlertCircle size={18} aria-hidden="true" /><div><strong>Something went wrong</strong><span>{message}</span></div>{action}</div> }
export function Section({ title, description, children, action }: { title: string; description?: string; children: ReactNode; action?: ReactNode }) {
  return <section className="section"><div className="section-head"><div><h2>{title}</h2>{description && <p>{description}</p>}</div>{action}</div>{children}</section>
}
