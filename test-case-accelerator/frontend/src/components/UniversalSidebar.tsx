import { useState, useEffect } from 'react'
import { 
  LayoutGrid, 
  Folder,
  FileText, 
  BookOpen, 
  Layers, 
  Settings as SettingsIcon, 
  Sparkles,
  PanelLeftClose,
  PanelLeftOpen
} from 'lucide-react'

interface UniversalSidebarProps {
  collapsed?: boolean;
  onToggleCollapse?: () => void;
}

export function UniversalSidebar({ collapsed = false, onToggleCollapse }: UniversalSidebarProps) {
  const isEmbedded = typeof window !== 'undefined' && (window.self !== window.top || window.location.search.includes('embedded=true'));
  if (isEmbedded) return null;

  const [internalCollapsed, setInternalCollapsed] = useState(() => {
    try {
      const saved = localStorage.getItem('sidebar_collapsed');
      if (saved !== null) return saved === 'true';
    } catch (error) {
      void error;
    }
    return collapsed;
  });

  useEffect(() => {
    setInternalCollapsed(collapsed);
  }, [collapsed]);

  const isCollapsed = onToggleCollapse ? collapsed : internalCollapsed;

  const toggle = () => {
    if (onToggleCollapse) {
      onToggleCollapse();
    } else {
      setInternalCollapsed((prev) => {
        const next = !prev;
        try {
          localStorage.setItem('sidebar_collapsed', String(next));
        } catch (error) {
          void error;
        }
        return next;
      });
    }
  };

  const [themeSidebarBg, setThemeSidebarBg] = useState(() => {
    try {
      return localStorage.getItem('storyforge_sidebar_bg') || '#1B1B3A';
    } catch {
      return '#1B1B3A';
    }
  });
  const [themeGradient, setThemeGradient] = useState(() => {
    try {
      const start = localStorage.getItem('storyforge_gradient_start') || '#FF5722';
      const end = localStorage.getItem('storyforge_gradient_end') || '#5924E1';
      return `linear-gradient(to right, ${start}, ${end})`;
    } catch {
      return 'linear-gradient(to right, #FF5722, #7B3FE4, #5924E1)';
    }
  });

  useEffect(() => {
    const syncTheme = () => {
      try {
        const bg = localStorage.getItem('storyforge_sidebar_bg');
        if (bg) setThemeSidebarBg(bg);
        const start = localStorage.getItem('storyforge_gradient_start');
        const end = localStorage.getItem('storyforge_gradient_end');
        if (start && end) {
          setThemeGradient(`linear-gradient(to right, ${start}, ${end})`);
        }
      } catch {}
    };
    syncTheme();
    window.addEventListener('storage', syncTheme);
    return () => window.removeEventListener('storage', syncTheme);
  }, []);

  const activeAccelerator = 'Backend Unit-Testcase Generator';

  const menuItems = [
    { 
      label: 'User Story', 
      icon: LayoutGrid, 
      path: '/dashboard',
    },
    { 
      label: 'UI Code', 
      icon: Folder, 
      path: '/ui-code',
    },
    { 
      label: 'API Code', 
      icon: FileText, 
      path: '/api-code/',
    },
    { 
      label: 'Unit Test Cases', 
      icon: BookOpen, 
      path: '/unit-test-cases/',
    },
    { 
      label: 'Application Testing', 
      icon: Layers, 
      path: '/application-testing/',
    },
    { 
      label: 'Backend Unit-Testcase Generator', 
      icon: Sparkles, 
      path: '/backend-unit-testcase-generator/',
    },
  ];

  return (
    <aside 
      style={{
        width: isCollapsed ? '78px' : '260px',
        height: '100vh',
        backgroundColor: themeSidebarBg,
        position: 'fixed',
        top: 0,
        left: 0,
        zIndex: 40,
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'space-between',
        padding: '24px 12px',
        boxSizing: 'border-box',
        borderRight: '1px solid rgba(45, 55, 72, 0.5)',
        userSelect: 'none',
        flexShrink: 0,
        transition: 'width 0.2s ease'
      }}
    >
      <div style={{ display: 'flex', flexDirection: 'column', gap: '28px' }}>
        {/* StoryForge AI Header with Collapse Toggle */}
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: isCollapsed ? 'center' : 'space-between', padding: '0 4px' }}>
          <a href="/dashboard" style={{ display: 'flex', alignItems: 'center', gap: '12px', textDecoration: 'none' }} title="StoryForge AI">
            <div style={{
              width: '34px',
              height: '34px',
              borderRadius: '12px',
              background: 'linear-gradient(to right, #FF602B, #4318FF)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              boxShadow: '0 4px 14px rgba(67, 24, 255, 0.4)',
              flexShrink: 0
            }}>
              <Sparkles size={18} color="#ffffff" style={{ fill: '#ffffff' }} />
            </div>
            {!isCollapsed && (
              <span style={{
                fontSize: '18px',
                fontWeight: 800,
                color: '#ffffff',
                letterSpacing: '-0.025em',
                fontFamily: 'Inter, sans-serif',
                whiteSpace: 'nowrap'
              }}>
                StoryForge AI
              </span>
            )}
          </a>

          {!isCollapsed && (
            <button
              onClick={toggle}
              title="Collapse sidebar"
              style={{
                border: 'none',
                background: 'transparent',
                color: '#A0AEC0',
                padding: '6px',
                borderRadius: '8px',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center'
              }}
            >
              <PanelLeftClose size={16} />
            </button>
          )}
        </div>

        {isCollapsed && (
          <div style={{ display: 'flex', justifyContent: 'center' }}>
            <button
              onClick={toggle}
              title="Expand sidebar"
              style={{
                border: 'none',
                background: 'transparent',
                color: '#A0AEC0',
                padding: '6px',
                borderRadius: '8px',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center'
              }}
            >
              <PanelLeftOpen size={16} />
            </button>
          </div>
        )}

        {/* Universal Sidebar Menu Items */}
        <nav style={{ display: 'flex', flexDirection: 'column', gap: '8px', padding: 0 }}>
          {menuItems.map((item) => {
            const isActive = activeAccelerator === item.label;
            return (
              <a
                key={item.label}
                href={item.path}
                title={isCollapsed ? item.label : undefined}
                onClick={(e) => {
                  if (isActive) {
                    e.preventDefault();
                  }
                }}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: isCollapsed ? 'center' : 'space-between',
                  padding: isCollapsed ? '12px' : '12px 14px',
                  borderRadius: '12px',
                  fontSize: '13px',
                  fontWeight: 600,
                  textDecoration: 'none',
                  transition: 'all 0.2s',
                  background: isActive ? themeGradient : 'transparent',
                  color: isActive ? '#ffffff' : '#8F9BBA',
                  boxShadow: isActive ? '0 4px 14px rgba(91, 50, 245, 0.35)' : 'none'
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: '12px', justifyContent: isCollapsed ? 'center' : 'flex-start' }}>
                  <item.icon size={18} color={isActive ? '#ffffff' : '#8F9BBA'} style={{ flexShrink: 0 }} />
                  {!isCollapsed && <span>{item.label}</span>}
                </div>
                {isActive && !isCollapsed && (
                  <span style={{
                    width: '5px',
                    height: '16px',
                    backgroundColor: '#ffffff',
                    borderRadius: '9999px',
                    flexShrink: 0
                  }} />
                )}
              </a>
            );
          })}
        </nav>
      </div>

      {/* Bottom Settings & User Avatar ('N') */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '16px', paddingTop: '16px', borderTop: '1px solid rgba(255, 255, 255, 0.1)', alignItems: isCollapsed ? 'center' : 'stretch' }}>
        <a
          href="/settings"
          title={isCollapsed ? 'Settings' : undefined}
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: isCollapsed ? 'center' : 'space-between',
            padding: isCollapsed ? '12px' : '12px 16px',
            borderRadius: '16px',
            fontSize: '12px',
            fontWeight: 700,
            color: '#A0AEC0',
            textDecoration: 'none',
            transition: 'all 0.2s'
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px', justifyContent: isCollapsed ? 'center' : 'flex-start' }}>
            <SettingsIcon size={16} color="#A0AEC0" style={{ flexShrink: 0 }} />
            {!isCollapsed && <span>Settings</span>}
          </div>
        </a>

        <div style={{
          width: '36px',
          height: '36px',
          borderRadius: '50%',
          backgroundColor: '#1A1A2E',
          border: '1px solid rgba(75, 85, 99, 0.6)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          color: '#ffffff',
          fontWeight: 800,
          fontSize: '12px',
          boxShadow: '0 2px 4px rgba(0,0,0,0.2)'
        }}>
          N
        </div>
      </div>
    </aside>
  );
}
