'use client';

import { useEffect, useState, type ReactNode } from 'react';
import Link from 'next/link';
import { usePathname, useRouter } from 'next/navigation';
import { AnimatePresence, motion, useMotionValue, useReducedMotion, useSpring } from 'framer-motion';
import {
  Bell,
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
  PanelLeftOpen
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

      {/* TOP NAVIGATION BAR & CONTENT WRAPPER */}
      <div style={{ marginLeft: sidebarCollapsed ? '78px' : '260px', flex: 1, minWidth: 0, display: 'flex', flexDirection: 'column', transition: 'margin-left 0.2s ease' }}>
        {/* Top Header */}
        <header className="sticky top-0 z-30 flex h-16 items-center justify-between border-b border-border/60 bg-background/90 px-6 backdrop-blur-md transition-colors gap-4">
          {/* Top Module Navigation Tabs */}
          <nav className="flex items-center gap-1.5 p-1 bg-muted/60 dark:bg-muted/30 border border-border/60 rounded-2xl">
            {moduleTabs.map(({ href, label, icon: Icon, exact }) => {
              const cleanCurrent = (pathname || '').replace(/^\/application-testing/, '').replace(/\/$/, '') || '/';
              const cleanTarget = href.replace(/\/$/, '') || '/';
              const active = exact ? cleanCurrent === cleanTarget : cleanCurrent.startsWith(cleanTarget);

              return (
                <Link
                  key={href}
                  href={href}
                  style={
                    active
                      ? {
                          backgroundColor: '#FF5523',
                          color: '#ffffff',
                          boxShadow: '0 4px 14px rgba(255, 85, 35, 0.35)',
                        }
                      : undefined
                  }
                  className={`inline-flex items-center gap-2 px-3.5 py-1.5 rounded-xl text-xs font-semibold transition-all cursor-pointer ${
                    active
                      ? 'bg-[#FF5523] hover:bg-[#E0481B] text-white shadow-md shadow-[#FF5523]/30'
                      : 'text-muted-foreground hover:text-foreground hover:bg-background/60'
                  }`}
                >
                  <Icon className="h-3.5 w-3.5" />
                  <span>{label}</span>
                </Link>
              );
            })}
          </nav>

          <div className="flex items-center gap-3 ml-auto">
            {/* Search Input */}
            <form onSubmit={handleGlobalSearch} className="relative w-64 hidden xl:block">
              <Search className="absolute left-3.5 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-muted-foreground" />
              <input
                type="text"
                value={globalQuery}
                onChange={(e) => setGlobalQuery(e.target.value)}
                placeholder="Search projects..."
                className="h-9 w-full rounded-full border border-border/70 bg-card/60 pl-9 pr-4 text-xs text-foreground placeholder:text-muted-foreground outline-none focus:border-primary focus:ring-2 focus:ring-primary/10 transition"
              />
            </form>

            {/* Quick Create Action */}
            <button
              onClick={() => setShowNewProjectModal(true)}
              className="inline-flex items-center gap-1.5 rounded-full bg-gradient-to-r from-[#FF602B] to-[#4318FF] px-4 py-2 text-xs font-bold text-white shadow-md shadow-[#FF602B]/25 hover:opacity-95 transition cursor-pointer"
            >
              <Plus className="h-3.5 w-3.5" /> New Project
            </button>

            {/* Notification Bell with Badge */}
            <button className="p-2 text-muted-foreground hover:text-foreground hover:bg-muted/50 rounded-full transition-colors relative cursor-pointer">
              <Bell className="h-4 w-4" />
              <span className="absolute top-1.5 right-1.5 h-2 w-2 bg-[#FF602B] rounded-full" />
            </button>

            <ThemeToggle />

            {/* Profile Section Standard */}
            <div className="flex items-center gap-2.5 pl-2 border-l border-border/60">
              <img
                src="https://images.unsplash.com/photo-1494790108377-be9c29b29330?auto=format&fit=crop&q=80&w=120"
                alt="Sarah Jenkins"
                className="h-8 w-8 rounded-full object-cover border border-border/70 shadow-xs"
              />
              <div className="hidden lg:flex flex-col text-left">
                <span className="text-xs font-bold text-foreground leading-tight">Sarah Jenkins</span>
                <span className="text-[10px] font-medium text-muted-foreground">Product Owner</span>
              </div>
            </div>
          </div>
        </header>

        {/* Route Content Container */}
        <main className="flex-1 px-8 py-6 max-w-7xl w-full mx-auto">
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
