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
  { label: 'API Code', icon: FileText, path: '/api-code' },
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

  useEffect(() => {
    try {
      const saved = localStorage.getItem('sidebar_collapsed');
      if (saved !== null) setSidebarCollapsed(saved === 'true');
    } catch {}
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
  const pointerX = useMotionValue(0);
  const pointerY = useMotionValue(0);
  const x = useSpring(pointerX, { stiffness: 38, damping: 24, mass: 1.2 });
  const y = useSpring(pointerY, { stiffness: 38, damping: 24, mass: 1.2 });

  useEffect(() => {
    if (reducedMotion) return;
    const move = (event: PointerEvent) => {
      pointerX.set((event.clientX / window.innerWidth - 0.5) * 34);
      pointerY.set((event.clientY / window.innerHeight - 0.5) * 34);
    };
    window.addEventListener('pointermove', move, { passive: true });
    return () => window.removeEventListener('pointermove', move);
  }, [pointerX, pointerY, reducedMotion]);

  const handleGlobalSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (globalQuery.trim()) {
      router.push(`/dashboard?q=${encodeURIComponent(globalQuery.trim())}`);
    }
  };

  const activeAccelerator = 'Application Testing';

  return (
    <div className={styles.experience} style={{ display: 'flex', minHeight: '100vh', backgroundColor: 'var(--background)' }}>
      <div className={styles.ambient} aria-hidden="true">
        <div className={styles.grid} />
        <motion.div className={styles.orb} style={reducedMotion ? undefined : { x, y }} />
        <div className={styles.ring} />
      </div>

      {/* UNIVERSAL STORYFORGE AI SIDEBAR */}
      <aside
        style={{
          width: sidebarCollapsed ? '78px' : '260px',
          height: '100vh',
          backgroundColor: '#1B1B3A',
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
                    background: isActive ? 'linear-gradient(to right, #FF5722, #7B3FE4, #5924E1)' : 'transparent',
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

        {/* Bottom Forge Stories Banner & Settings */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', paddingTop: '16px', borderTop: '1px solid rgba(255, 255, 255, 0.1)', alignItems: sidebarCollapsed ? 'center' : 'stretch' }}>
          {!sidebarCollapsed && (
            <div style={{
              background: 'linear-gradient(135deg, rgba(255, 96, 43, 0.15) 0%, rgba(67, 24, 255, 0.15) 100%)',
              border: '1px solid rgba(255, 255, 255, 0.1)',
              borderRadius: '16px',
              padding: '14px',
              color: '#ffffff',
              boxShadow: '0 4px 16px rgba(0,0,0,0.2)'
            }}>
              <div style={{ fontSize: '12px', fontWeight: 800, color: '#ffffff', display: 'flex', alignItems: 'center', gap: '6px' }}>
                <Sparkles size={14} color="#FF602B" /> Forge Stories
              </div>
              <div style={{ fontSize: '10px', color: '#A0AEC0', marginTop: '4px', lineHeight: '1.4' }}>
                Generate AI-powered stories faster
              </div>
              <a
                href="/dashboard"
                style={{
                  display: 'inline-block',
                  marginTop: '10px',
                  padding: '6px 14px',
                  background: 'linear-gradient(to right, #FF602B, #4318FF)',
                  color: '#ffffff',
                  fontSize: '10px',
                  fontWeight: 700,
                  borderRadius: '10px',
                  textDecoration: 'none',
                  textAlign: 'center'
                }}
              >
                Try Now
              </a>
            </div>
          )}

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
        </div>
      </aside>

      {/* TOP NAVIGATION BAR & CONTENT WRAPPER */}
      <div style={{ marginLeft: sidebarCollapsed ? '78px' : '260px', flex: 1, minWidth: 0, display: 'flex', flexDirection: 'column', transition: 'margin-left 0.2s ease' }}>
        {/* Top Header Bar (Matching User Story Header) */}
        <header className="sticky top-0 z-30 flex items-center justify-between px-8 py-3.5 bg-white/95 dark:bg-card/95 backdrop-blur-md border-b border-border shrink-0 shadow-xs">
          <form onSubmit={handleGlobalSearch} className="flex-1 max-w-md relative">
            <Search className="w-4 h-4 absolute left-3.5 top-1/2 -translate-y-1/2 text-muted-foreground" />
            <input
              type="text"
              value={globalQuery}
              onChange={(e) => setGlobalQuery(e.target.value)}
              placeholder="Search projects, test cases..."
              className="w-full pl-10 pr-4 py-2 text-xs bg-muted/40 border border-border rounded-xl focus:outline-none focus:ring-2 focus:ring-[#7551FF] text-foreground placeholder:text-muted-foreground"
            />
          </form>

          <div className="flex items-center gap-4">
            <button className="p-2 text-muted-foreground hover:text-foreground hover:bg-muted rounded-xl transition-colors relative cursor-pointer">
              <Bell className="w-4 h-4" />
              <span className="absolute top-1.5 right-1.5 w-2 h-2 bg-[#FF602B] rounded-full" />
            </button>

            <ThemeToggle />

            <div className="flex items-center gap-3 pl-3 border-l border-border">
              <img
                src="https://images.unsplash.com/photo-1494790108377-be9c29b29330?auto=format&fit=crop&q=80&w=120"
                alt="Sarah Jenkins"
                className="w-9 h-9 rounded-full object-cover border border-border shadow-sm"
              />
              <div className="flex flex-col text-left">
                <span className="text-xs font-bold text-foreground leading-tight">Sarah Jenkins</span>
                <span className="text-[11px] text-muted-foreground">Product Owner</span>
              </div>
            </div>
          </div>
        </header>

        {/* Sticky In-Page Workflow Tab Navigation (for sub-routes) */}
        {(() => {
          const cleanCurrent = (pathname || '').replace(/^\/application-testing/, '').replace(/\/$/, '') || '/';
          if (cleanCurrent === '/' || cleanCurrent === '/dashboard') return null;

          return (
            <div className="sticky top-[57px] z-20 bg-background/95 backdrop-blur-md px-8 pt-3 pb-0 flex items-center gap-2 overflow-x-auto border-b border-border/80">
              {moduleTabs.map(({ href, label, exact }) => {
                const targetClean = href.replace(/\/$/, '') || '/';
                const active = exact ? cleanCurrent === targetClean : cleanCurrent.startsWith(targetClean);

                return (
                  <Link
                    key={href}
                    href={href}
                    className={`px-5 py-2.5 text-xs font-bold rounded-t-lg rounded-b-none transition-all duration-150 whitespace-nowrap cursor-pointer ${
                      active
                        ? 'bg-[#FF602B] text-white shadow-none'
                        : 'bg-[#EAEBED] text-[#505D6F] dark:bg-muted/50 dark:text-muted-foreground hover:bg-[#DFE1E6] hover:text-[#111827] dark:hover:bg-muted dark:hover:text-foreground'
                    }`}
                  >
                    {label}
                  </Link>
                );
              })}
            </div>
          );
        })()}

        {/* Route Content Container (Full Width, No Outer Side Gap) */}
        <main className="flex-1 px-8 py-5 w-full">
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
