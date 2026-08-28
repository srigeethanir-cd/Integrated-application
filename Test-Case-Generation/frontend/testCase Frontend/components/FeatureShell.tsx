'use client';

import { useEffect, useState, type ReactNode } from 'react';
import Link from 'next/link';
import { usePathname, useRouter } from 'next/navigation';
import { AnimatePresence, motion, useMotionValue, useReducedMotion, useSpring } from 'framer-motion';
import {
  Folder,
  FileText,
  BookOpen,
  Layers,
  Code2,
  FileCheck2,
  FolderKanban,
  LayoutGrid,
  Plus,
  Search,
  Settings as SettingsIcon,
  Sparkles,
  Terminal,
  CheckSquare,
  PanelLeftClose,
  PanelLeftOpen,
  Bell
} from 'lucide-react';
import { ThemeToggle } from '@/components/theme-toggle';
import { NewProjectModal } from '@/components/projects/NewProjectModal';
import { ScrollToBottomButton } from './ScrollToBottomButton';
import styles from './PremiumShell.module.css';

const universalMenuItems = [
  { label: 'User Story', icon: LayoutGrid, path: '/dashboard' },
  { label: 'UI Code', icon: Folder, path: '/ui-code' },
  { label: 'API Code', icon: FileText, path: '/api-code/' },
  { label: 'Unit Test Cases', icon: BookOpen, path: '/unit-test-cases/' },
  { label: 'Application Testing', icon: Layers, path: '/application-testing/' },
  { label: 'Backend Unit-Testcase Generator', icon: Sparkles, path: '/backend-unit-testcase-generator/' },
];

const moduleTabs = [
  { href: '/dashboard', label: 'Dashboard', icon: FolderKanban, exact: true },
  { href: '/test-case-generation', label: 'New Generator', icon: Plus, exact: true },
  { href: '/test-case-generation/results', label: 'Generated Tests', icon: FileCheck2, exact: false },
  { href: '/test-case-generation/automation', label: 'Playwright Studio', icon: Code2, exact: false },
  { href: '/test-case-generation/url-crawler', label: 'App Crawler', icon: Sparkles, exact: false },
];

export function FeatureShell({ children }: { children: ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const [showNewProjectModal, setShowNewProjectModal] = useState(false);
  const [globalQuery, setGlobalQuery] = useState('');
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);

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
    try {
      const saved = localStorage.getItem('sidebar_collapsed');
      if (saved !== null) setSidebarCollapsed(saved === 'true');
    } catch {}

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

  const toggleSidebar = () => {
    setSidebarCollapsed((prev) => {
      const next = !prev;
      try {
        localStorage.setItem('sidebar_collapsed', String(next));
      } catch {}
      return next;
    });
  };

  const reducedMotion = useReducedMotion();

  const handleGlobalSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (globalQuery.trim()) {
      router.push(`/dashboard?q=${encodeURIComponent(globalQuery.trim())}`);
    }
  };

  const activeAccelerator = 'Application Testing';
  const isEmbedded = typeof window !== 'undefined' && (window.self !== window.top || window.location.search.includes('embedded=true'));

  return (
    <div style={{ display: 'flex', minHeight: '100vh', backgroundColor: '#F7F9FC' }} className="dark:bg-[#0B1121]">

      {/* UNIVERSAL STORYFORGE AI SIDEBAR */}
      {!isEmbedded && (
      <aside
        style={{
          width: sidebarCollapsed ? '78px' : '260px',
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
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: sidebarCollapsed ? 'center' : 'space-between', padding: '0 4px' }}>
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
              {!sidebarCollapsed && (
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

            {!sidebarCollapsed && (
              <button
                onClick={toggleSidebar}
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

          {sidebarCollapsed && (
            <div style={{ display: 'flex', justifyContent: 'center' }}>
              <button
                onClick={toggleSidebar}
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
            {universalMenuItems.map((item) => {
              const isActive = activeAccelerator === item.label;
              return (
                <a
                  key={item.label}
                  href={item.path}
                  title={sidebarCollapsed ? item.label : undefined}
                  onClick={(e) => {
                    if (isActive) {
                      e.preventDefault();
                    }
                  }}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: sidebarCollapsed ? 'center' : 'space-between',
                    padding: sidebarCollapsed ? '12px' : '12px 14px',
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
                  <div style={{ display: 'flex', alignItems: 'center', gap: '12px', justifyContent: sidebarCollapsed ? 'center' : 'flex-start' }}>
                    <item.icon size={18} color={isActive ? '#ffffff' : '#8F9BBA'} style={{ flexShrink: 0 }} />
                    {!sidebarCollapsed && <span>{item.label}</span>}
                  </div>
                  {isActive && !sidebarCollapsed && (
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
        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px', paddingTop: '16px', borderTop: '1px solid rgba(255, 255, 255, 0.1)', alignItems: sidebarCollapsed ? 'center' : 'stretch' }}>
          <a
            href="/settings"
            title={sidebarCollapsed ? 'Settings' : undefined}
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: sidebarCollapsed ? 'center' : 'space-between',
              padding: sidebarCollapsed ? '12px' : '12px 16px',
              borderRadius: '16px',
              fontSize: '12px',
              fontWeight: 700,
              color: '#A0AEC0',
              textDecoration: 'none',
              transition: 'all 0.2s'
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px', justifyContent: sidebarCollapsed ? 'center' : 'flex-start' }}>
              <SettingsIcon size={16} color="#A0AEC0" style={{ flexShrink: 0 }} />
              {!sidebarCollapsed && <span>Settings</span>}
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
      )}

      {/* TOP NAVIGATION BAR & CONTENT WRAPPER */}
      <div style={{ marginLeft: isEmbedded ? 0 : (sidebarCollapsed ? '78px' : '260px'), flex: 1, minWidth: 0, display: 'flex', flexDirection: 'column', transition: 'margin-left 0.2s ease' }}>
        {/* Top Header (Matching User Story Reference exactly) */}
        <header className="sticky top-0 z-30 flex h-16 items-center justify-between border-b border-[#E5E7EB] dark:border-gray-800 bg-white/95 dark:bg-[#111827]/95 px-8 backdrop-blur-md transition-colors gap-4">
          {/* Global Search Input on the Left (Matching User Story Reference) */}
          <form onSubmit={handleGlobalSearch} className="relative flex-1 max-w-md">
            <Search className="absolute left-3.5 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-[#A0AEC0] pointer-events-none" />
            <input
              type="text"
              value={globalQuery}
              onChange={(e) => setGlobalQuery(e.target.value)}
              placeholder="Search projects, stories..."
              className="w-full pl-10 pr-4 py-2 text-xs bg-[#F8F9FC] border border-[#E5E7EB] rounded-xl text-[#111827] dark:text-white dark:bg-[#1E293B] dark:border-gray-700 outline-none focus:ring-2 focus:ring-[#7551FF]/20 focus:border-[#7551FF] transition"
            />
          </form>

          {/* Right Controls: Bell notification, ThemeToggle, Sarah Jenkins profile */}
          <div className="flex items-center gap-3 ml-auto">
            {/* Notification Bell with Orange Dot */}
            <button
              aria-label="Notifications"
              className="relative p-2 text-[#6B7280] hover:text-[#111827] dark:hover:text-white rounded-xl transition cursor-pointer"
            >
              <Bell className="w-4 h-4" />
              <span className="absolute top-1.5 right-1.5 w-2 h-2 bg-[#FF602B] rounded-full" />
            </button>

            <ThemeToggle />

            {/* Profile Section Standard */}
            <div className="flex items-center gap-2.5 pl-3 border-l border-[#E5E7EB] dark:border-gray-700">
              <img
                src="https://images.unsplash.com/photo-1494790108377-be9c29b29330?auto=format&fit=crop&q=80&w=120"
                alt="Sarah Jenkins"
                className="h-8 w-8 rounded-full object-cover border border-[#E5E7EB] shadow-xs"
              />
              <div className="hidden lg:flex flex-col text-left">
                <span className="text-xs font-bold text-[#111827] dark:text-white leading-tight">Sarah Jenkins</span>
                <span className="text-[10px] font-medium text-[#A0AEC0]">Product Owner</span>
              </div>
            </div>
          </div>
        </header>

        {/* Route Content Container */}
        <main className="flex-1 px-8 py-5 space-y-4 w-full bg-[#F7F9FC] dark:bg-[#0B1121] min-h-[calc(100vh-64px)]">
          {/* If NOT on dashboard, render Workflow Tabs at top of main */}
          {!((pathname || '').replace(/^\/application-testing/, '').replace(/\/$/, '') === '' || (pathname || '').replace(/^\/application-testing/, '').replace(/\/$/, '') === '/dashboard') && (
            <div className="pt-2 pb-0 flex items-center gap-2 overflow-x-auto border-b border-[#E5E7EB]/80 mb-4">
              {moduleTabs.map(({ href, label, exact }) => {
                const cleanCurrent = (pathname || '').replace(/^\/application-testing/, '').replace(/\/$/, '') || '/';
                const cleanTarget = href.replace(/\/$/, '') || '/';
                const active = exact ? cleanCurrent === cleanTarget : cleanCurrent.startsWith(cleanTarget);

                return (
                  <Link
                    key={href}
                    href={href}
                    className={`px-5 py-2.5 text-xs font-bold rounded-t-lg rounded-b-none transition-all duration-150 whitespace-nowrap cursor-pointer ${
                      active
                        ? 'bg-[#FF602B] text-white shadow-none'
                        : 'bg-[#EAEBED] text-[#505D6F] hover:bg-[#DFE1E6] hover:text-[#111827]'
                    }`}
                  >
                    {label}
                  </Link>
                );
              })}
            </div>
          )}
          <AnimatePresence mode="wait" initial={false}>
            <motion.div
              key={pathname}
              className={styles.route}
              initial={reducedMotion ? false : { opacity: 0, y: 16, filter: 'blur(6px)' }}
              animate={{ opacity: 1, y: 0, filter: 'blur(0px)' }}
              exit={reducedMotion ? undefined : { opacity: 0, y: -10, filter: 'blur(4px)' }}
              transition={{ duration: reducedMotion ? 0 : 0.4, ease: [0.22, 1, 0.36, 1] }}
            >
              {children}
            </motion.div>
          </AnimatePresence>
        </main>
      </div>

      <ScrollToBottomButton />
      <NewProjectModal isOpen={showNewProjectModal} onClose={() => setShowNewProjectModal(false)} />
    </div>
  );
}
