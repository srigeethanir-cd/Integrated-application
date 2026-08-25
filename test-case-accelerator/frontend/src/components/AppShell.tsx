import { useEffect, useState, type ComponentType } from 'react'
import { ArrowLeft, BarChart3, Bot, ChevronDown, CircleUserRound, FolderKanban, History, Home, Menu, Moon, PanelLeftClose, PanelLeftOpen, PlayCircle, Settings, Sun, X, Zap } from 'lucide-react'
import { NavLink, Outlet, useNavigate } from 'react-router-dom'
import { useAppState } from '../state/app-state'
import { UploadModal } from './UploadModal'

type NavigationItem = {
  label: string
  to: string
  icon: ComponentType<{ size?: number }>
  projectRoute?: boolean
}

const workspace: NavigationItem[] = [
  { label: 'Projects', to: '/projects', icon: FolderKanban },
  { label: 'AI Workspace', to: '/processing', icon: Bot, projectRoute: true },
  { label: 'Runtime Validation', to: '/runtime-validation', icon: PlayCircle, projectRoute: true },
]
const insights: NavigationItem[] = [
  { label: 'Reports', to: '/reports', icon: BarChart3 },
  { label: 'History', to: '/history', icon: History },
]
const system: NavigationItem[] = [{ label: 'Settings', to: '/settings', icon: Settings }]

export function AppShell() {
  const state = useAppState()
  const navigate = useNavigate()
  const [mobile, setMobile] = useState(false)
  const [collapsed, setCollapsed] = useState(() => localStorage.getItem('sidebarCollapsed') === 'true')
  const [dark, setDark] = useState(() => localStorage.getItem('theme') === 'dark')
  useEffect(() => { void state.refreshProjects().catch(() => undefined) }, [])
  useEffect(() => { document.documentElement.dataset.theme = dark ? 'dark' : 'light'; localStorage.setItem('theme', dark ? 'dark' : 'light') }, [dark])
  const toggleCollapsed = () => { setCollapsed((value) => { localStorage.setItem('sidebarCollapsed', String(!value)); return !value }) }
  const activeProject = state.projects.find((project) => project.id === state.activeProjectId)
  const projectStatus = activeProject?.status === 'FAILED' ? 'Failed' : activeProject?.status === 'PROCESSING' ? 'Running' : 'Ready'
  const statusTone = projectStatus.toLowerCase()
  const closeMobile = () => setMobile(false)
  const navigationLink = ({ label, to, icon: Icon, projectRoute }: NavigationItem) => {
    const target = projectRoute ? (state.activeProjectId ? `${to}/${state.activeProjectId}` : '/projects') : to
    return <NavLink end={to === '/'} key={label} to={target} title={collapsed ? label : undefined} onClick={closeMobile} className={({ isActive }) => isActive ? 'active' : ''}><Icon size={17} /><span>{label}</span></NavLink>
  }

  return <div className={`app-shell ${collapsed ? 'sidebar-collapsed' : ''}`}>
    <a className="skip-link" href="#main-content">Skip to main content</a>
    <aside className={`sidebar ${mobile ? 'open' : ''}`} aria-label="Application sidebar">
      <div className="brand"><span><Zap size={18} /></span><div><strong>TestForge AI</strong><small>Generate • Validate • Export</small></div><button className="mobile-close" aria-label="Close navigation" onClick={closeMobile}><X size={18} /></button></div>
      <nav aria-label="Primary navigation">
        <div className="nav-dashboard">{navigationLink({ label: 'Dashboard', to: '/', icon: Home })}</div>
        <section className="nav-group" aria-labelledby="workspace-navigation"><small className="nav-label" id="workspace-navigation">Workspace</small>{workspace.map(navigationLink)}</section>
        <section className="nav-group" aria-labelledby="insights-navigation"><small className="nav-label" id="insights-navigation">Insights</small>{insights.map(navigationLink)}</section>
        <section className="nav-group" aria-labelledby="system-navigation"><small className="nav-label" id="system-navigation">System</small>{system.map(navigationLink)}</section>
      </nav>
      <a
        href="/dashboard"
        className="collapse-control"
        style={{ marginBottom: '8px', color: '#ff602b', textDecoration: 'none' }}
      >
        <ArrowLeft size={17} />
        <span>Return to StoryForge AI</span>
      </a>
      <button className="collapse-control" onClick={toggleCollapsed} aria-label={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}>{collapsed ? <PanelLeftOpen size={17} /> : <PanelLeftClose size={17} />}<span>Collapse sidebar</span></button>
    </aside>
    {mobile && <button className="sidebar-scrim" aria-label="Close navigation" onClick={closeMobile} />}
    <div className="app-body">
      <header className="topbar">
        <button className="mobile-menu" aria-label="Open navigation" onClick={() => setMobile(true)}><Menu size={20} /></button>
        <div className="topbar-context"><small>Current Project</small><button className="project-select" onClick={() => navigate('/projects')}><span>{activeProject?.name ?? 'Select a project'}</span>{activeProject && <i className={`project-status-dot ${statusTone}`} aria-hidden="true" />}<em>{activeProject ? projectStatus : ''}</em>{activeProject?.updated_at && <time dateTime={activeProject.updated_at}>{new Date(activeProject.updated_at).toLocaleDateString()}</time>}<ChevronDown size={14} /></button></div>
        <div className="topbar-spacer" />
        <button className="icon-button" aria-label="Toggle color theme" onClick={() => setDark(!dark)}>{dark ? <Sun size={18} /> : <Moon size={18} />}</button>
        <button className="profile" aria-label="Open user profile"><CircleUserRound size={22} /></button>
      </header>
      <main id="main-content"><Outlet /></main>
    </div>
    <UploadModal />
  </div>
}
