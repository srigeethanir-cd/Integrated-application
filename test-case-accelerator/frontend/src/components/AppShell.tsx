import { useEffect, useState, type ComponentType } from 'react'
import { BarChart3, Bot, ChevronDown, FolderKanban, History, Home, Moon, PlayCircle, Settings, Sun } from 'lucide-react'
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
    <div className="app-shell" style={{ display: 'flex', minHeight: '100vh', backgroundColor: 'var(--canvas, #F7F9FC)' }}>
      {/* StoryForge AI Universal Sidebar */}
      <UniversalSidebar />

      {/* Main Content Area with Fixed Navigation & Scrollable Body */}
      <div className="app-body" style={{ marginLeft: '260px', flex: 1, minWidth: 0, display: 'flex', flexDirection: 'column', height: '100vh', overflowY: 'auto' }}>
        {/* Sticky Top Header with Module Navigation Tabs */}
        <header
          className="topbar"
          style={{
            height: '64px',
            position: 'sticky',
            top: 0,
            zIndex: 30,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            gap: '16px',
            padding: '0 32px',
            borderBottom: '1px solid var(--border, #E5E7EB)',
            background: dark ? '#172033' : '#ffffff',
            boxShadow: '0 1px 2px rgba(0,0,0,0.02)',
            flexShrink: 0
          }}
        >
          {/* Top Module Navigation Tabs Bar */}
          <nav
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              padding: '4px',
              borderRadius: '8px',
              backgroundColor: dark ? '#111827' : '#F7F9FC',
              border: '1px solid var(--border, #E5E7EB)'
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
                    padding: '6px 14px',
                    borderRadius: '6px',
                    fontSize: '12px',
                    fontWeight: 700,
                    textDecoration: 'none',
                    transition: 'all 0.15s ease',
                    backgroundColor: isActive ? '#FF602B' : 'transparent',
                    color: isActive ? '#ffffff' : dark ? '#A0AEC0' : '#6B7280',
                    boxShadow: isActive ? '0 2px 8px rgba(255, 96, 43, 0.35)' : 'none',
                    cursor: 'pointer'
                  })}
                >
                  <Icon size={14} />
                  <span>{label}</span>
                </NavLink>
              )
            })}
          </nav>

          {/* Right Header: Project Selector & Profile Avatar Standard */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <button
              className="project-select"
              onClick={() => navigate('/projects')}
              style={{
                height: '36px',
                borderRadius: '9999px',
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                padding: '0 14px',
                border: '1px solid var(--border, #E5E7EB)',
                backgroundColor: dark ? '#1E293B' : '#F7F9FC',
                color: dark ? '#E5EDF7' : '#111827',
                fontSize: '12px',
                fontWeight: 600,
                cursor: 'pointer'
              }}
            >
              <span>{activeProject?.name ?? 'Select a project'}</span>
              {activeProject && <i className={`project-status-dot ${statusTone}`} aria-hidden="true" />}
              <ChevronDown size={14} />
            </button>

            <button
              className="icon-button"
              aria-label="Toggle color theme"
              onClick={() => setDark(!dark)}
              style={{
                width: '36px',
                height: '36px',
                borderRadius: '50%',
                border: '1px solid var(--border, #E5E7EB)',
                backgroundColor: dark ? '#1E293B' : '#ffffff',
                color: dark ? '#FFB800' : '#6B7280',
                display: 'grid',
                placeItems: 'center',
                cursor: 'pointer'
              }}
            >
              {dark ? <Sun size={16} /> : <Moon size={16} />}
            </button>

            <div style={{ display: 'flex', alignItems: 'center', gap: '10px', paddingLeft: '8px', borderLeft: '1px solid var(--border, #E5E7EB)' }}>
              <img
                src="https://images.unsplash.com/photo-1494790108377-be9c29b29330?auto=format&fit=crop&q=80&w=120"
                alt="Sarah Jenkins"
                style={{ width: '34px', height: '34px', borderRadius: '50%', objectFit: 'cover', border: '1px solid #E5E7EB' }}
              />
              <div style={{ display: 'flex', flexDirection: 'column', textAlign: 'left' }}>
                <span style={{ fontSize: '12px', fontWeight: 700, color: dark ? '#FFFFFF' : '#111827', lineHeight: 1.2 }}>Sarah Jenkins</span>
                <span style={{ fontSize: '10px', color: '#A0AEC0' }}>Product Owner</span>
              </div>
            </div>
          </div>
        </header>

        {/* Main Content Area - Scrollable */}
        <main id="main-content" style={{ flex: 1, minHeight: 0 }}>
          <Outlet />
        </main>
      </div>

      <UploadModal />
    </div>
  )
}
