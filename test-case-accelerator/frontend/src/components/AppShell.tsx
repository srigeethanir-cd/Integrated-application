import { useEffect, useState, type ComponentType } from 'react'
import { BarChart3, Bot, ChevronDown, CircleUserRound, FolderKanban, History, Home, Moon, PlayCircle, Settings, Sun } from 'lucide-react'
import { NavLink, Outlet, useNavigate } from 'react-router-dom'
import { useAppState } from '../state/app-state'
import { UploadModal } from './UploadModal'
import { UniversalSidebar } from './UniversalSidebar'

type NavigationItem = {
  label: string
  to: string
  icon: ComponentType<{ size?: number }>
  projectRoute?: boolean
}

const navTabs: NavigationItem[] = [
  { label: 'Dashboard', to: '/', icon: Home },
  { label: 'Projects', to: '/projects', icon: FolderKanban },
  { label: 'AI Workspace', to: '/processing', icon: Bot, projectRoute: true },
  { label: 'Runtime Validation', to: '/runtime-validation', icon: PlayCircle, projectRoute: true },
  { label: 'Reports', to: '/reports', icon: BarChart3 },
  { label: 'History', to: '/history', icon: History },
  { label: 'Settings', to: '/settings', icon: Settings },
]

export function AppShell() {
  const state = useAppState()
  const navigate = useNavigate()
  const [dark, setDark] = useState(() => localStorage.getItem('theme') === 'dark')

  useEffect(() => { void state.refreshProjects().catch(() => undefined) }, [])
  useEffect(() => {
    document.documentElement.dataset.theme = dark ? 'dark' : 'light'
    localStorage.setItem('theme', dark ? 'dark' : 'light')
  }, [dark])

  const activeProject = state.projects.find((project) => project.id === state.activeProjectId)
  const projectStatus = activeProject?.status === 'FAILED' ? 'Failed' : activeProject?.status === 'PROCESSING' ? 'Running' : 'Ready'
  const statusTone = projectStatus.toLowerCase()

  return (
    <div className="app-shell" style={{ display: 'flex', minHeight: '100vh', backgroundColor: 'var(--canvas)' }}>
      {/* StoryForge AI Universal Sidebar */}
      <UniversalSidebar />

      {/* Main Content Area */}
      <div className="app-body" style={{ marginLeft: '260px', flex: 1, minWidth: 0, display: 'flex', flexDirection: 'column' }}>
        {/* Top Header with Module Navigation Tabs */}
        <header
          className="topbar"
          style={{
            height: '68px',
            position: 'sticky',
            top: 0,
            zIndex: 20,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            gap: '16px',
            padding: '0 28px',
            borderBottom: '1px solid var(--border)',
            background: dark ? '#172033' : 'rgba(255,255,255,0.96)',
            backdropFilter: 'blur(8px)'
          }}
        >
          {/* Top Module Navigation Tabs Bar */}
          <nav
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              padding: '4px',
              borderRadius: '16px',
              backgroundColor: dark ? '#111827' : '#F4F7FE',
              border: '1px solid var(--border)'
            }}
          >
            {navTabs.map(({ label, to, icon: Icon, projectRoute }) => {
              const target = projectRoute ? (state.activeProjectId ? `${to}/${state.activeProjectId}` : '/projects') : to
              return (
                <NavLink
                  end={to === '/'}
                  key={label}
                  to={target}
                  style={({ isActive }) => ({
                    display: 'inline-flex',
                    alignItems: 'center',
                    gap: '7px',
                    padding: '7px 14px',
                    borderRadius: '12px',
                    fontSize: '12px',
                    fontWeight: 650,
                    textDecoration: 'none',
                    transition: 'all 0.15s ease',
                    backgroundColor: isActive ? '#FF5523' : 'transparent',
                    color: isActive ? '#ffffff' : dark ? '#A0AEC0' : '#707EAE',
                    boxShadow: isActive ? '0 4px 14px rgba(255, 85, 35, 0.3)' : 'none',
                    cursor: 'pointer'
                  })}
                >
                  <Icon size={15} />
                  <span>{label}</span>
                </NavLink>
              )
            })}
          </nav>

          {/* Right Header Controls */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <div className="topbar-context">
              <button
                className="project-select"
                onClick={() => navigate('/projects')}
                style={{
                  height: '38px',
                  borderRadius: '12px',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '10px',
                  padding: '0 12px',
                  border: '1px solid var(--border)',
                  backgroundColor: dark ? '#1E293B' : '#ffffff',
                  color: dark ? '#E5EDF7' : '#334155',
                  fontSize: '12px',
                  fontWeight: 600,
                  cursor: 'pointer'
                }}
              >
                <span>{activeProject?.name ?? 'Select a project'}</span>
                {activeProject && <i className={`project-status-dot ${statusTone}`} aria-hidden="true" />}
                <em>{activeProject ? projectStatus : ''}</em>
                <ChevronDown size={14} />
              </button>
            </div>

            <button
              className="icon-button"
              aria-label="Toggle color theme"
              onClick={() => setDark(!dark)}
              style={{
                width: '38px',
                height: '38px',
                borderRadius: '12px',
                border: '1px solid var(--border)',
                backgroundColor: dark ? '#1E293B' : '#ffffff',
                color: dark ? '#FFB800' : '#526074',
                display: 'grid',
                placeItems: 'center',
                cursor: 'pointer'
              }}
            >
              {dark ? <Sun size={17} /> : <Moon size={17} />}
            </button>

            <button
              className="profile"
              aria-label="Open user profile"
              style={{
                width: '38px',
                height: '38px',
                borderRadius: '12px',
                border: '1px solid var(--border)',
                backgroundColor: dark ? '#1E293B' : '#ffffff',
                color: '#64748b',
                display: 'grid',
                placeItems: 'center',
                cursor: 'pointer'
              }}
            >
              <CircleUserRound size={20} />
            </button>
          </div>
        </header>

        {/* Main Content Area */}
        <main id="main-content" style={{ flex: 1, minHeight: 0 }}>
          <Outlet />
        </main>
      </div>

      <UploadModal />
    </div>
  )
}
