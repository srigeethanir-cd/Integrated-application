import React, { useState, useEffect } from 'react';
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
} from 'lucide-react';

const DEFAULTS = {
  sidebar_bg: '#1B1B3A',
  highlight_from: '#FF5722',
  highlight_via: '#7B3FE4',
  logo_url: null,
  logo_shape: 'rounded',
};

function getLogoRadius(shape) {
  if (shape === 'square') return '0px';
  if (shape === 'circle') return '50%';
  return '8px';
}

function applyCssVars(bg, from, via, shape) {
  if (typeof document !== 'undefined' && document.documentElement) {
    document.documentElement.style.setProperty('--sidebar-background', bg);
    document.documentElement.style.setProperty('--sidebar-highlight-from', from);
    document.documentElement.style.setProperty('--sidebar-highlight-via', via);
    document.documentElement.style.setProperty('--logo-border-radius', getLogoRadius(shape));
  }
}

function useSidebarPersonalization() {
  const [colors, setColors] = useState(() => {
    if (typeof window === 'undefined') return DEFAULTS;
    try {
      const bg = localStorage.getItem('app_sidebar_bg') || DEFAULTS.sidebar_bg;
      const from = localStorage.getItem('app_highlight_from') || DEFAULTS.highlight_from;
      const via = localStorage.getItem('app_highlight_via') || DEFAULTS.highlight_via;
      const logo = localStorage.getItem('app_custom_logo') || null;
      const shape = localStorage.getItem('app_logo_shape') || DEFAULTS.logo_shape;
      applyCssVars(bg, from, via, shape);
      return {
        sidebar_bg: bg,
        highlight_from: from,
        highlight_via: via,
        logo_url: logo,
        logo_shape: shape,
      };
    } catch {
      return DEFAULTS;
    }
  });

  useEffect(() => {
    const handleData = (d) => {
      const next = {
        sidebar_bg: d.sidebar_bg || DEFAULTS.sidebar_bg,
        highlight_from: d.highlight_from || DEFAULTS.highlight_from,
        highlight_via: d.highlight_via || DEFAULTS.highlight_via,
        logo_url: d.logo_url || null,
        logo_shape: d.logo_shape || DEFAULTS.logo_shape,
      };
      setColors(next);
      applyCssVars(next.sidebar_bg, next.highlight_from, next.highlight_via, next.logo_shape);
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
      .then(json => handleData(json.data || json))
      .catch(() => {});

    let socket = null;
    let reconnectTimer = null;
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
              handleData(parsed.data);
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

export default function Sidebar() {
  const [collapsed, setCollapsed] = useState(false);
  const colors = useSidebarPersonalization();

  useEffect(() => {
    try {
      const saved = localStorage.getItem('sidebar_collapsed');
      if (saved !== null) setCollapsed(saved === 'true');
    } catch {
      // Ignore localStorage errors
    }
  }, []);

  const toggleCollapsed = () => {
    setCollapsed((prev) => {
      const next = !prev;
      try {
        localStorage.setItem('sidebar_collapsed', String(next));
      } catch {
        // Ignore localStorage errors
      }
      return next;
    });
  };

  const activeAccelerator = 'Unit Test Cases';

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
      className={`${collapsed ? 'w-[78px]' : 'w-[260px]'} h-screen select-none shrink-0 z-30 flex flex-col justify-between py-6 px-3 relative border-r border-[#2D3748]/50 transition-all duration-200`} 
      style={{ backgroundColor: colors.sidebar_bg }}
    >
      <div className="space-y-7">
        {/* StoryForge AI Header with Collapse Toggle */}
        <div className={`flex items-center ${collapsed ? 'justify-center' : 'justify-between'} px-1`}>
          <a href="/dashboard" className="flex items-center gap-3 group" title="StoryForge AI">
            {colors.logo_url ? (
              <div 
                className="w-8.5 h-8.5 bg-white/10 p-1 flex items-center justify-center shrink-0 shadow-md group-hover:scale-105 transition-all overflow-hidden"
                style={{ borderRadius: logoRadius }}
              >
                <img src={colors.logo_url} alt="Logo" className="w-full h-full object-contain" />
              </div>
            ) : (
              <div
                className="w-8.5 h-8.5 flex items-center justify-center shrink-0 shadow-lg shadow-purple-950/60 group-hover:scale-105 transition-all"
                style={{ background: activeGradient, borderRadius: logoRadius }}
              >
                <Sparkles className="w-4.5 h-4.5 text-white fill-white" />
              </div>
            )}
            {!collapsed && (
              <span className="text-lg font-extrabold text-white tracking-tight font-sans whitespace-nowrap">
                StoryForge AI
              </span>
            )}
          </a>

          {!collapsed && (
            <button
              onClick={toggleCollapsed}
              title="Collapse sidebar"
              className="p-1.5 rounded-xl text-[#A0AEC0] hover:text-white hover:bg-white/10 transition-colors cursor-pointer"
            >
              <PanelLeftClose className="w-4 h-4" />
            </button>
          )}
        </div>

        {collapsed && (
          <div className="flex justify-center">
            <button
              onClick={toggleCollapsed}
              title="Expand sidebar"
              className="p-1.5 rounded-xl text-[#A0AEC0] hover:text-white hover:bg-white/10 transition-colors cursor-pointer"
            >
              <PanelLeftOpen className="w-4 h-4" />
            </button>
          </div>
        )}

        {/* Sidebar Menu Items */}
        <nav className="space-y-2">
          {menuItems.map((item) => {
            const isActive = activeAccelerator === item.label;

            return (
              <a
                key={item.label}
                href={item.path}
                className={`flex items-center ${collapsed ? 'justify-center p-3' : 'justify-between px-3.5 py-3'} rounded-xl text-xs transition-all duration-200 group relative ${
                  isActive
                    ? 'text-white shadow-md'
                    : 'text-[#8F9BBA] hover:text-white hover:bg-white/10'
                }`}
                style={isActive ? { background: activeGradient } : undefined}
                title={collapsed ? item.label : undefined}
              >
                <div className={`flex items-center ${collapsed ? 'justify-center w-full' : 'gap-3'}`}>
                  <item.icon className={`w-5 h-5 shrink-0 ${isActive ? 'text-white' : 'text-[#8F9BBA] group-hover:text-white'}`} />
                  {!collapsed && <span className="font-semibold text-sm">{item.label}</span>}
                </div>

                {/* Active Indicator Bar | */}
                {isActive && !collapsed && (
                  <span className="w-1.5 h-4 bg-white rounded-full shrink-0 shadow-xs" />
                )}
              </a>
            );
          })}
        </nav>
      </div>

      {/* Bottom Settings & User Avatar ('N') */}
      <div className={`space-y-4 pt-4 border-t border-white/10 flex flex-col ${collapsed ? 'items-center' : ''}`}>
        <a
          href="/settings"
          title={collapsed ? 'Settings' : undefined}
          className={`flex items-center ${collapsed ? 'justify-center p-3' : 'justify-between px-4 py-3'} rounded-2xl text-xs font-bold transition-all duration-200 w-full group text-[#A0AEC0] hover:text-white hover:bg-white/10`}
        >
          <div className={`flex items-center ${collapsed ? 'justify-center' : 'gap-3'}`}>
            <SettingsIcon className="w-4 h-4 shrink-0 text-[#A0AEC0] group-hover:text-white" />
            {!collapsed && <span>Settings</span>}
          </div>
        </a>

        <div className="w-9 h-9 rounded-full bg-[#1A1A2E] border border-gray-700/60 flex items-center justify-center text-white font-extrabold text-xs shadow-md">
          N
        </div>
      </div>
    </aside>
  );
}
