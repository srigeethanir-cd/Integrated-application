import { useEffect, useState } from 'react'
import { Bell, ChevronDown, Moon, Search, Sparkles, Sun } from 'lucide-react'
import { NavLink, Outlet, useLocation, useNavigate } from 'react-router-dom'
import { useAppState } from '../state/app-state'
import { UploadModal } from './UploadModal'
import { UniversalSidebar } from './UniversalSidebar'

type NavigationItem = {
  label: string
  to: string
  projectRoute?: boolean
}

const navTabs: NavigationItem[] = [
  { label: 'Dashboard', to: '/' },
  { label: 'Projects', to: '/projects' },
  { label: 'AI Workspace', to: '/processing', projectRoute: true },
  { label: 'Runtime Validation', to: '/runtime-validation', projectRoute: true },
  { label: 'Reports', to: '/reports' },
  { label: 'History', to: '/history' },
  { label: 'Settings', to: '/settings' },
]

export function AppShell() {
  const state = useAppState()
  const navigate = useNavigate()
  const location = useLocation()
  const isDashboard = location.pathname === '/' || location.pathname === ''
  const [searchQuery, setSearchQuery] = useState('')
  const [dark, setDark] = useState(() => localStorage.getItem('theme') === 'dark')
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
      <div className="app-body" style={{ marginLeft: sidebarCollapsed ? '78px' : '260px', flex: 1, minWidth: 0, display: 'flex', flexDirection: 'column', height: '100vh', overflowY: 'auto', transition: 'margin-left 0.2s ease' }}>
        {/* Sticky Top Header with Search Bar (Matching Reference Image 2) */}
        <header
          className="topbar"
          style={{
            height: '60px',
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
          {/* Search Bar matching Image 2 */}
          <div style={{ flex: 1, maxWidth: '420px', position: 'relative' }}>
            <Search
              size={15}
              style={{
                position: 'absolute',
                left: '14px',
                top: '50%',
                transform: 'translateY(-50%)',
                color: '#A0AEC0',
                pointerEvents: 'none'
              }}
            />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search projects, stories..."
              style={{
                width: '100%',
                paddingLeft: '40px',
                paddingRight: '16px',
                paddingTop: '8px',
                paddingBottom: '8px',
                fontSize: '12px',
                backgroundColor: dark ? '#1E293B' : '#F8F9FC',
                border: '1px solid var(--border, #E5E7EB)',
                borderRadius: '12px',
                outline: 'none',
                color: dark ? '#FFFFFF' : '#111827',
                fontFamily: 'inherit'
              }}
            />
          </div>

          {/* Right Header: Project Selector, Theme Toggle, Notification Bell, Profile */}
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

            {/* Notification Bell with Orange Dot */}
            <button
              aria-label="Notifications"
              style={{
                width: '36px',
                height: '36px',
                borderRadius: '12px',
                border: 'none',
                backgroundColor: 'transparent',
                color: dark ? '#A0AEC0' : '#6B7280',
                display: 'grid',
                placeItems: 'center',
                position: 'relative',
                cursor: 'pointer'
              }}
            >
              <Bell size={18} />
              <span
                style={{
                  position: 'absolute',
                  top: '6px',
                  right: '6px',
                  width: '8px',
                  height: '8px',
                  backgroundColor: '#FF602B',
                  borderRadius: '50%'
                }}
              />
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
                style={{ width: '36px', height: '36px', borderRadius: '50%', objectFit: 'cover', border: '1px solid #E5E7EB', boxShadow: '0 1px 2px rgba(0,0,0,0.05)' }}
              />
              <div style={{ display: 'flex', flexDirection: 'column', textAlign: 'left' }}>
                <span style={{ fontSize: '12px', fontWeight: 700, color: dark ? '#FFFFFF' : '#111827', lineHeight: 1.2 }}>Sarah Jenkins</span>
                <span style={{ fontSize: '10px', color: '#A0AEC0' }}>Product Owner</span>
              </div>
            </div>
          </div>
        </header>

        {/* Main Content Area - Full Width & Space Aligned */}
        <main
          id="main-content"
          style={{
            flex: 1,
            minHeight: 0,
            padding: '20px 32px 40px',
            width: '100%',
            display: 'flex',
            flexDirection: 'column',
            gap: '16px'
          }}
        >
          {/* Welcome Banner & Action Button: only on Dashboard '/' */}
          {isDashboard && (
            <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', flexWrap: 'wrap', gap: '16px' }}>
              <div>
                <h1 style={{ fontSize: '24px', fontWeight: 800, color: 'var(--text, #111827)', letterSpacing: '-0.025em', margin: 0 }}>
                  Good morning, Sarah
                </h1>
                <p style={{ fontSize: '13px', color: 'var(--muted, #6B7280)', marginTop: '4px', margin: 0 }}>
                  Welcome back to your workspace. Let&apos;s forge some amazing unit tests today.
                </p>
              </div>

              {/* + New Project Button (Matching Image 2 & 3: rounded-xl, gradient, + New Project) */}
              <button
                onClick={() => state.openUpload('zip')}
                style={{
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: '8px',
                  padding: '10px 22px',
                  background: 'linear-gradient(to right, #FF602B, #7551FF)',
                  color: '#ffffff',
                  fontSize: '12px',
                  fontWeight: 700,
                  borderRadius: '12px',
                  border: 'none',
                  boxShadow: '0 2px 8px rgba(255, 96, 43, 0.25)',
                  cursor: 'pointer',
                  transition: 'opacity 0.2s'
                }}
              >
                <Sparkles size={15} />
                <span>+ New Project</span>
              </button>
            </div>
          )}

          {/* Workflow Tab Navigation Bar (Placed BELOW Good morning, Sarah as in Image 2 & 3) */}
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              overflowX: 'auto',
              borderBottom: '1px solid var(--border, #E5E7EB)',
              paddingBottom: '0',
              width: '100%'
            }}
          >
            {navTabs.map(({ label, to, projectRoute }) => {
              const target = projectRoute ? (state.activeProjectId ? `${to}/${state.activeProjectId}` : '/projects') : to
              return (
                <NavLink
                  end={to === '/'}
                  key={label}
                  to={target}
                  style={({ isActive }) => ({
                    display: 'inline-flex',
                    alignItems: 'center',
                    padding: '10px 20px',
                    borderRadius: '8px 8px 0 0',
                    fontSize: '12px',
                    fontWeight: 700,
                    textDecoration: 'none',
                    whiteSpace: 'nowrap',
                    transition: 'all 0.15s ease',
                    backgroundColor: isActive ? '#FF602B' : '#EAEBED',
                    color: isActive ? '#ffffff' : '#505D6F',
                    cursor: 'pointer'
                  })}
                >
                  <span>{label}</span>
                </NavLink>
              )
            })}
          </div>

          <Outlet />
        </main>
      </div>

      <UploadModal />
    </div>
  )
}
