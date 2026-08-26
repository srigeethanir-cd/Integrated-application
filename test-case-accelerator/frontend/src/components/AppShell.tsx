import { useEffect, useState, type ComponentType } from 'react'
import { BarChart3, Bell, Bot, FolderKanban, History, Home, Moon, PlayCircle, Search, Settings, Sun } from 'lucide-react'
import { NavLink, Outlet, useLocation, useNavigate } from 'react-router-dom'
import { useAppState } from '../state/app-state'
import { UploadModal } from './UploadModal'
import { UniversalSidebar } from './UniversalSidebar'

export type NavigationItem = {
  label: string
  to: string
  icon: ComponentType<{ size?: number }>
  projectRoute?: boolean
}

export const navTabs: NavigationItem[] = [
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
  const [sidebarCollapsed, setSidebarCollapsed] = useState(() => {
    try { return localStorage.getItem('sidebar_collapsed') === 'true' } catch { return false }
  })
  const [globalSearch, setGlobalSearch] = useState('')

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

  const handleSearchKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' && globalSearch.trim()) {
      navigate(`/projects?q=${encodeURIComponent(globalSearch.trim())}`)
    }
  }

  return (
    <div className="app-shell" style={{ display: 'flex', minHeight: '100vh', backgroundColor: 'var(--canvas, #F7F9FC)' }}>
      {/* StoryForge AI Universal Sidebar */}
      <UniversalSidebar collapsed={sidebarCollapsed} onToggleCollapse={toggleSidebar} />

      {/* Main Content Area with Fixed Navigation & Scrollable Body */}
      <div className="app-body" style={{ marginLeft: sidebarCollapsed ? '78px' : '260px', flex: 1, minWidth: 0, display: 'flex', flexDirection: 'column', height: '100vh', overflowY: 'auto', transition: 'margin-left 0.2s ease' }}>
        {/* Sticky Top Header with Search Bar on Left, Bell & Profile on Right */}
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
          {/* Left Search Bar (Matches User Story Page Header) */}
          <div style={{ flex: 1, maxWidth: '420px', position: 'relative' }}>
            <Search size={16} color="#A0AEC0" style={{ position: 'absolute', left: '14px', top: '50%', transform: 'translateY(-50%)' }} />
            <input
              type="text"
              placeholder="Search projects, test cases..."
              value={globalSearch}
              onChange={(e) => setGlobalSearch(e.target.value)}
              onKeyDown={handleSearchKeyDown}
              style={{
                width: '100%',
                paddingLeft: '38px',
                paddingRight: '16px',
                paddingTop: '8px',
                paddingBottom: '8px',
                fontSize: '12px',
                backgroundColor: dark ? '#111827' : '#F8F9FC',
                border: '1px solid var(--border, #E5E7EB)',
                borderRadius: '12px',
                color: dark ? '#FFFFFF' : '#111827',
                outline: 'none',
                boxSizing: 'border-box'
              }}
            />
          </div>

          {/* Right Header: Notification Bell, Theme Toggle, Sarah Jenkins Profile */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
            <button
              style={{
                padding: '8px',
                color: dark ? '#A0AEC0' : '#6B7280',
                background: 'transparent',
                border: 'none',
                borderRadius: '12px',
                cursor: 'pointer',
                position: 'relative',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center'
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
                width: '34px',
                height: '34px',
                borderRadius: '50%',
                border: '1px solid var(--border, #E5E7EB)',
                backgroundColor: dark ? '#1E293B' : '#ffffff',
                color: dark ? '#FFB800' : '#6B7280',
                display: 'grid',
                placeItems: 'center',
                cursor: 'pointer'
              }}
            >
              {dark ? <Sun size={15} /> : <Moon size={15} />}
            </button>

            <div style={{ display: 'flex', alignItems: 'center', gap: '10px', paddingLeft: '12px', borderLeft: '1px solid var(--border, #E5E7EB)' }}>
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

        {/* Sticky In-Page Navigation for sub-routes (when not on dashboard) */}
        {location.pathname !== '/' && (
          <div
            style={{
              position: 'sticky',
              top: '60px',
              zIndex: 20,
              backgroundColor: dark ? 'rgba(23, 32, 51, 0.95)' : 'rgba(247, 249, 252, 0.95)',
              backdropFilter: 'blur(8px)',
              padding: '10px 32px 0 32px',
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              overflowX: 'auto',
              borderBottom: '1px solid var(--border, #E5E7EB)'
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
                    padding: '10px 20px',
                    fontSize: '12px',
                    fontWeight: 700,
                    borderTopLeftRadius: '8px',
                    borderTopRightRadius: '8px',
                    borderBottomLeftRadius: 0,
                    borderBottomRightRadius: 0,
                    textDecoration: 'none',
                    transition: 'all 0.15s ease',
                    backgroundColor: isActive ? '#FF602B' : dark ? '#1E293B' : '#EAEBED',
                    color: isActive ? '#ffffff' : dark ? '#A0AEC0' : '#505D6F',
                    whiteSpace: 'nowrap',
                    cursor: 'pointer'
                  })}
                >
                  {label}
                </NavLink>
              )
            })}
          </div>
        )}

        {/* Main Content Area - Scrollable */}
        <main id="main-content" style={{ flex: 1, minHeight: 0, width: '100%' }}>
          <Outlet />
        </main>
      </div>

      <UploadModal />
    </div>
  )
}
