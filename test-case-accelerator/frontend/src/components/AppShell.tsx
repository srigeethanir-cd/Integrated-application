import { useEffect, useState, type ComponentType } from 'react'
import { BarChart3, Bell, Bot, ChevronDown, FolderKanban, History, Home, Moon, PlayCircle, Plus, Search, Settings, Sparkles, Sun } from 'lucide-react'
import { NavLink, Outlet, useNavigate, useLocation } from 'react-router-dom'
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
  const location = useLocation()
  const [dark, setDark] = useState(() => localStorage.getItem('theme') === 'dark')
  const [searchTerm, setSearchTerm] = useState('')
  const [sidebarCollapsed, setSidebarCollapsed] = useState(() => {
    try { return localStorage.getItem('sidebar_collapsed') === 'true' } catch { return false }
  })

  useEffect(() => { void state.refreshProjects().catch(() => undefined) }, [])
  useEffect(() => {
    document.documentElement.dataset.theme = dark ? 'dark' : 'light'
    localStorage.setItem('theme', dark ? 'dark' : 'light')
  }, [dark])

  const toggleSidebar = () => {
    setSidebarCollapsed((prev) => {
      const next = !prev
      try { localStorage.setItem('sidebar_collapsed', String(next)) } catch {}
      return next
    })
  }

  const activeProject = state.projects.find((project) => project.id === state.activeProjectId)
  const projectStatus = activeProject?.status === 'FAILED' ? 'Failed' : activeProject?.status === 'PROCESSING' ? 'Running' : 'Ready'
  const statusTone = projectStatus.toLowerCase()

  return (
    <div className="app-shell" style={{ display: 'flex', minHeight: '100vh', backgroundColor: 'var(--canvas, #F7F9FC)' }}>
      {/* StoryForge AI Universal Sidebar */}
      <UniversalSidebar collapsed={sidebarCollapsed} onToggleCollapse={toggleSidebar} />

      {/* Main Content Area with Fixed Navigation & Scrollable Body */}
      <div className="app-body" style={{ marginLeft: sidebarCollapsed ? '78px' : '260px', flex: 1, minWidth: 0, display: 'flex', flexDirection: 'column', minHeight: '100vh', transition: 'margin-left 0.2s ease' }}>
        {/* Sticky Top Header with Search & Profile */}
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
          {/* Search Bar matching User Story Template */}
          <div style={{ flex: 1, maxWidth: '420px', position: 'relative' }}>
            <Search size={15} style={{ position: 'absolute', left: '14px', top: '50%', transform: 'translateY(-50%)', color: '#A0AEC0' }} />
            <input
              type="text"
              placeholder="Search projects, test cases..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              style={{
                width: '100%',
                paddingLeft: '38px',
                paddingRight: '16px',
                paddingTop: '8px',
                paddingBottom: '8px',
                fontSize: '12px',
                backgroundColor: dark ? '#111827' : '#F7F9FC',
                border: '1px solid var(--border, #E5E7EB)',
                borderRadius: '9999px',
                outline: 'none',
                color: dark ? '#ffffff' : '#111827'
              }}
            />
          </div>

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
              aria-label="Notifications"
              style={{
                width: '36px',
                height: '36px',
                borderRadius: '50%',
                border: '1px solid var(--border, #E5E7EB)',
                backgroundColor: dark ? '#1E293B' : '#ffffff',
                color: '#6B7280',
                display: 'grid',
                placeItems: 'center',
                cursor: 'pointer',
                position: 'relative'
              }}
            >
              <Bell size={16} />
              <span style={{ position: 'absolute', top: '6px', right: '6px', width: '8px', height: '8px', backgroundColor: '#FF602B', borderRadius: '50%' }} />
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

        {/* Main Workspace Body */}
        <main
          id="main-content"
          style={{
            flex: 1,
            padding: '24px 32px',
            maxWidth: '1280px',
            width: '100%',
            margin: '0 auto',
            display: 'flex',
            flexDirection: 'column',
            gap: '20px'
          }}
        >
          {/* Welcome Banner & Action Button Row */}
          <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', flexWrap: 'wrap', gap: '16px' }}>
            <div>
              <h1 style={{ fontSize: '24px', fontWeight: 800, color: 'var(--text, #111827)', letterSpacing: '-0.025em', margin: 0 }}>
                Good morning, Sarah
              </h1>
              <p style={{ fontSize: '13px', color: 'var(--muted, #6B7280)', marginTop: '4px', margin: 0 }}>
                Welcome back to your workspace. Let&apos;s forge some amazing unit tests today.
              </p>
            </div>

            <button
              onClick={() => state.openUpload('zip')}
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: '8px',
                padding: '10px 24px',
                background: 'linear-gradient(to right, #FF602B, #4318FF)',
                color: '#ffffff',
                fontSize: '12px',
                fontWeight: 800,
                borderRadius: '9999px',
                border: 'none',
                boxShadow: '0 4px 16px rgba(255, 96, 43, 0.35)',
                cursor: 'pointer',
                transition: 'opacity 0.2s'
              }}
            >
              <Sparkles size={15} />
              New Project
            </button>
          </div>

          {/* Module Navigation Tabs Bar - Positioned after Welcome & New Project Button */}
          <nav
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              padding: '6px 0',
              overflowX: 'auto',
              borderBottom: '1px solid var(--border, #E5E7EB)'
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
                    padding: '7px 16px',
                    borderRadius: '8px',
                    fontSize: '12px',
                    fontWeight: 700,
                    textDecoration: 'none',
                    transition: 'all 0.15s ease',
                    backgroundColor: isActive ? '#FF602B' : dark ? '#1E293B' : '#ffffff',
                    color: isActive ? '#ffffff' : dark ? '#A0AEC0' : '#6B7280',
                    border: isActive ? 'none' : '1px solid var(--border, #E5E7EB)',
                    boxShadow: isActive ? '0 2px 8px rgba(255, 96, 43, 0.35)' : 'none',
                    cursor: 'pointer',
                    whiteSpace: 'nowrap'
                  })}
                >
                  <Icon size={14} />
                  <span>{label}</span>
                </NavLink>
              )
            })}
          </nav>

          {/* Outlet Page Content */}
          <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: '20px' }}>
            <Outlet />
          </div>
        </main>
      </div>

      <UploadModal />
    </div>
  )
}
