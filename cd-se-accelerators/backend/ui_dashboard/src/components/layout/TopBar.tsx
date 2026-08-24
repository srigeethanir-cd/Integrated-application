import React, { useState, useRef, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { clsx } from 'clsx';
import { Button, Badge } from '@/components/ui';
import { BellIcon, SearchIcon, PlusIcon } from '@/components/icons';
import { useApprovalStatus } from '@/hooks/useDashboard';
import { usePipelineStatus } from '@/hooks/useDashboard';
import { formatDistanceToNow } from 'date-fns';
import type { Notification } from '@/services/types';

// ─── Notification panel ───────────────────────────────────────────────────────

function buildNotifications(
  approvalStatus: string | undefined,
  pipelineStatus: string | undefined,
  currentAgent: string | undefined,
): Notification[] {
  const notes: Notification[] = [];

  if (approvalStatus === 'PENDING') {
    notes.push({
      id:        'approval-pending',
      type:      'approval',
      message:   'Blueprint is awaiting your review and approval.',
      timestamp: new Date().toISOString(),
      read:      false,
    });
  }

  if (
    pipelineStatus &&
    ['RUNNING_STAGE_1', 'RUNNING_STAGE_2', 'GENERATING'].includes(pipelineStatus)
  ) {
    notes.push({
      id:        'pipeline-running',
      type:      'workflow',
      message:   `Pipeline running — current agent: ${currentAgent ?? 'Unknown'}.`,
      timestamp: new Date().toISOString(),
      read:      false,
    });
  }

  if (pipelineStatus === 'PAUSED_FOR_FINAL_APPROVAL') {
    notes.push({
      id:        'final-approval',
      type:      'approval',
      message:   'Final governance approval is required to deploy.',
      timestamp: new Date().toISOString(),
      read:      false,
    });
  }

  return notes;
}

const notifIcon: Record<Notification['type'], React.ReactNode> = {
  approval: (
    <div className="w-8 h-8 rounded-full bg-status-warningBg flex items-center justify-center flex-shrink-0">
      <svg className="w-4 h-4 text-status-warning" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
          d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
      </svg>
    </div>
  ),
  workflow: (
    <div className="w-8 h-8 rounded-full bg-primary-50 flex items-center justify-center flex-shrink-0">
      <svg className="w-4 h-4 text-primary-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
          d="M13 10V3L4 14h7v7l9-11h-7z" />
      </svg>
    </div>
  ),
  info: (
    <div className="w-8 h-8 rounded-full bg-status-infoBg flex items-center justify-center flex-shrink-0">
      <svg className="w-4 h-4 text-status-info" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
          d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
      </svg>
    </div>
  ),
  error: (
    <div className="w-8 h-8 rounded-full bg-status-dangerBg flex items-center justify-center flex-shrink-0">
      <svg className="w-4 h-4 text-status-danger" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
          d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
      </svg>
    </div>
  ),
};

const NotificationPanel: React.FC<{
  notifications: Notification[];
  onClose: () => void;
}> = ({ notifications, onClose }) => {
  const panelRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (panelRef.current && !panelRef.current.contains(e.target as Node)) {
        onClose();
      }
    };
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, [onClose]);

  return (
    <div
      ref={panelRef}
      className="absolute right-0 top-full mt-2 w-80 bg-white rounded-2xl border border-surface-border shadow-card-hover z-50 animate-scale-in overflow-hidden"
      role="dialog"
      aria-label="Notifications"
    >
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-surface-border">
        <span className="text-sm font-bold text-ink">Notifications</span>
        {notifications.length > 0 && (
          <Badge variant="danger" size="sm">{notifications.length} new</Badge>
        )}
      </div>

      {/* Items */}
      <div className="max-h-72 overflow-y-auto divide-y divide-surface-border">
        {notifications.length === 0 ? (
          <div className="py-10 text-center">
            <p className="text-sm text-ink-muted">All caught up!</p>
          </div>
        ) : (
          notifications.map((n) => (
            <div key={n.id} className="flex items-start gap-3 px-4 py-3 hover:bg-surface-secondary transition-colors">
              {notifIcon[n.type]}
              <div className="flex-1 min-w-0">
                <p className="text-xs font-medium text-ink leading-relaxed">{n.message}</p>
                <p className="text-[11px] text-ink-muted mt-0.5">
                  {formatDistanceToNow(new Date(n.timestamp), { addSuffix: true })}
                </p>
              </div>
              {!n.read && (
                <span className="w-2 h-2 rounded-full bg-primary-500 flex-shrink-0 mt-1" aria-label="Unread" />
              )}
            </div>
          ))
        )}
      </div>

      {/* Footer */}
      <div className="px-4 py-2.5 border-t border-surface-border">
        <button className="text-xs font-semibold text-primary-600 hover:text-primary-700 transition-colors">
          View all notifications →
        </button>
      </div>
    </div>
  );
};

// ─── Search bar ───────────────────────────────────────────────────────────────

const SearchBar: React.FC = () => {
  const [focused, setFocused] = useState(false);
  const [query, setQuery]     = useState('');

  return (
    <div
      className={clsx(
        'relative flex items-center gap-2 px-3 py-2 rounded-xl border transition-all duration-200 bg-surface-secondary',
        focused
          ? 'border-primary-300 ring-2 ring-primary-100 bg-white'
          : 'border-surface-border hover:border-primary-200',
      )}
    >
      <SearchIcon className="w-4 h-4 text-ink-muted flex-shrink-0" />
      <input
        type="text"
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        onFocus={() => setFocused(true)}
        onBlur={() => setFocused(false)}
        placeholder="Search projects, epics, stories..."
        className="flex-1 bg-transparent text-sm text-ink placeholder-ink-muted outline-none min-w-0 w-56"
        aria-label="Search"
      />
      {/* Keyboard shortcut hint */}
      {!focused && query === '' && (
        <kbd className="hidden sm:inline-flex items-center px-1.5 py-0.5 rounded-md border border-surface-border text-[10px] font-mono text-ink-muted bg-white">
          /
        </kbd>
      )}
      {focused && query && (
        <button
          onMouseDown={(e) => e.preventDefault()}
          onClick={() => setQuery('')}
          className="text-ink-muted hover:text-ink transition-colors"
          aria-label="Clear search"
        >
          <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      )}
    </div>
  );
};

// ─── Main TopBar ──────────────────────────────────────────────────────────────

interface TopBarProps {
  greeting?: string;
  subtitle?: string;
}

export const TopBar: React.FC<TopBarProps> = ({
  greeting  = 'Hi, BA! 👋',
  subtitle  = "Here's what's happening across your projects today.",
}) => {
  const navigate = useNavigate();
  const [notifOpen, setNotifOpen] = useState(false);

  const { data: approvalData } = useApprovalStatus();
  const { data: pipelineData } = usePipelineStatus();

  const notifications = buildNotifications(
    approvalData?.status,
    pipelineData?.execution_status,
    pipelineData?.current_agent,
  );

  const unreadCount = notifications.filter((n) => !n.read).length;

  const closeNotif = useCallback(() => setNotifOpen(false), []);

  return (
    <header className="sticky top-0 z-30 bg-white border-b border-surface-border px-6 py-3">
      <div className="flex items-center justify-between gap-4">

        {/* Left: page greeting */}
        <div className="min-w-0">
          <h1 className="text-lg font-bold text-ink leading-tight truncate">{greeting}</h1>
          <p className="text-xs text-ink-muted mt-0.5 truncate">{subtitle}</p>
        </div>

        {/* Right: search + actions */}
        <div className="flex items-center gap-2 flex-shrink-0">
          <SearchBar />

          {/* Notification bell */}
          <div className="relative">
            <button
              onClick={() => setNotifOpen((v) => !v)}
              aria-label={`Notifications${unreadCount > 0 ? ` (${unreadCount} unread)` : ''}`}
              className={clsx(
                'relative w-9 h-9 rounded-xl flex items-center justify-center transition-all duration-150',
                notifOpen
                  ? 'bg-primary-50 text-primary-600'
                  : 'text-ink-secondary hover:bg-surface-secondary hover:text-ink',
              )}
            >
              <BellIcon className="w-5 h-5" />
              {unreadCount > 0 && (
                <span
                  className="absolute -top-0.5 -right-0.5 min-w-[18px] h-[18px] rounded-full bg-status-danger text-white text-[10px] font-bold flex items-center justify-center px-1"
                  aria-hidden
                >
                  {unreadCount > 9 ? '9+' : unreadCount}
                </span>
              )}
            </button>

            {notifOpen && (
              <NotificationPanel notifications={notifications} onClose={closeNotif} />
            )}
          </div>

          {/* New Project CTA */}
          <Button
            variant="primary"
            size="md"
            icon={<PlusIcon className="w-4 h-4" />}
            onClick={() => navigate('/projects/new')}
          >
            New Project
          </Button>
        </div>
      </div>
    </header>
  );
};
