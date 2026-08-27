import React, { useState, useEffect } from 'react'
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

const DEFAULTS = {
  sidebar_bg: '#1B1B3A',
  highlight_from: '#FF5722',
  highlight_via: '#7B3FE4',
  logo_url: null as string | null,
  logo_shape: 'rounded',
};

type SidebarColors = typeof DEFAULTS;

function getLogoRadius(shape: string): string {
  if (shape === 'square') return '0px';
  if (shape === 'circle') return '50%';
  return '8px';
}

function useSidebarPersonalization(): SidebarColors {
  const [colors, setColors] = useState<SidebarColors>(() => {
    if (typeof window === 'undefined') return DEFAULTS;
    try {
      return {
        sidebar_bg: localStorage.getItem('app_sidebar_bg') || DEFAULTS.sidebar_bg,
        highlight_from: localStorage.getItem('app_highlight_from') || DEFAULTS.highlight_from,
        highlight_via: localStorage.getItem('app_highlight_via') || DEFAULTS.highlight_via,
        logo_url: localStorage.getItem('app_custom_logo') || null,
        logo_shape: localStorage.getItem('app_logo_shape') || DEFAULTS.logo_shape,
      };
    } catch {
      return DEFAULTS;
    }
  });

  useEffect(() => {
    const applyData = (d: Record<string, string | null>) => {
      const next: SidebarColors = {
        sidebar_bg: d.sidebar_bg || DEFAULTS.sidebar_bg,
        highlight_from: d.highlight_from || DEFAULTS.highlight_from,
        highlight_via: d.highlight_via || DEFAULTS.highlight_via,
        logo_url: d.logo_url || null,
        logo_shape: d.logo_shape || DEFAULTS.logo_shape,
      };
      setColors(next);
      try {
        localStorage.setItem('app_sidebar_bg', next.sidebar_bg);
        localStorage.setItem('app_highlight_from', next.highlight_from);
        localStorage.setItem('app_highlight_via', next.highlight_via);
        localStorage.setItem('app_logo_shape', next.logo_shape);
        if (next.logo_url) localStorage.setItem('app_custom_logo', next.logo_url);
        else localStorage.removeItem('app_custom_logo');
      } catch {}
    };

    fetch('/api/settings/personalization', { credentials: 'omit' })
      .then(res => res.ok ? res.json() : Promise.reject(res))
      .then(json => applyData(json.data || json))
      .catch(() => {});

    let socket: WebSocket | null = null;
    let reconnectTimer: ReturnType<typeof setTimeout> | null = null;
    let cleaned = false;

    const connect = () => {
      try {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const host = window.location.host;
        socket = new WebSocket(`${protocol}//${host}/api/ws/settings`);

        socket.onmessage = (event) => {
          try {
            const parsed = JSON.parse(event.data);
            if (parsed.type === 'PERSONALIZATION_UPDATED' || parsed.type === 'INITIAL_PERSONALIZATION') {
              applyData(parsed.data);
            }
          } catch {}
        };

        socket.onclose = () => {
          if (!cleaned) reconnectTimer = setTimeout(connect, 4000);
        };
        socket.onerror = () => { socket?.close(); };
      } catch {
        if (!cleaned) reconnectTimer = setTimeout(connect, 4000);
      }
    };

    connect();

    return () => {
      cleaned = true;
      if (reconnectTimer) clearTimeout(reconnectTimer);
      if (socket) socket.close();
    };
  }, []);

  return colors;
}

export function UniversalSidebar({ collapsed = false, onToggleCollapse }: UniversalSidebarProps) {
  const [isCollapsed, setIsCollapsed] = useState(collapsed);
  const colors = useSidebarPersonalization();

  useEffect(() => {
    setIsCollapsed(collapsed);
  }, [collapsed]);

  const toggle = () => {
    if (onToggleCollapse) {
      onToggleCollapse();
    } else {
      setIsCollapsed((prev) => !prev);
    }
  };

  const activeAccelerator = 'Backend Unit-Testcase Generator';

  const menuItems = [
    { label: 'User Story', icon: LayoutGrid, path: '/dashboard' },
    { label: 'UI Code', icon: Folder, path: '/ui-code' },
    { label: 'API Code', icon: FileText, path: '/api-code' },
    { label: 'Unit Test Cases', icon: BookOpen, path: '/unit-test-cases/' },
    { label: 'Application Testing', icon: Layers, path: '/application-testing/' },
    { label: 'Backend Unit-Testcase Generator', icon: Sparkles, path: '/backend-unit-testcase-generator/' },
  ];

  const activeGradient = `linear-gradient(to right, ${colors.highlight_from}, ${colors.highlight_via})`;
  const logoRadius = getLogoRadius(colors.logo_shape);

  return (
    <aside 
      style={{
        width: isCollapsed ? '78px' : '260px',
        height: '100vh',
        backgroundColor: colors.sidebar_bg,
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
            {colors.logo_url ? (
              <div style={{
                width: '34px',
                height: '34px',
                borderRadius: logoRadius,
                background: 'rgba(255,255,255,0.1)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                padding: '4px',
                flexShrink: 0,
                overflow: 'hidden',
                transition: 'border-radius 0.2s ease',
              }}>
                <img src={colors.logo_url} alt="Logo" style={{ width: '100%', height: '100%', objectFit: 'contain' }} />
              </div>
            ) : (
              <div style={{
                width: '34px',
                height: '34px',
                borderRadius: logoRadius,
                background: activeGradient,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                boxShadow: '0 4px 14px rgba(67, 24, 255, 0.4)',
                flexShrink: 0,
                transition: 'border-radius 0.2s ease',
              }}>
                <Sparkles size={18} color="#ffffff" style={{ fill: '#ffffff' }} />
              </div>
            )}
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
                  background: isActive ? activeGradient : 'transparent',
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
