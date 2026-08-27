import React, { useState } from 'react';
import { NavLink, useLocation } from 'react-router-dom';
import { clsx } from 'clsx';
import { Avatar, Badge } from '@/components/ui';
import {
  HomeIcon,
  FolderIcon,
  ListIcon,
  CpuIcon,
  WorkspaceIcon,
  ArtifactIcon,
  TraceIcon,
  CheckIcon,
  ApprovalIcon,
  ReportIcon,
  SettingsIcon,
  AuditIcon,
  ChevronDownIcon,
} from '@/components/icons';
import { useDashboardSummary, useApprovalStatus } from '@/hooks/useDashboard';

// ─── Nav item types ───────────────────────────────────────────────────────────

interface NavItem {
  label: string;
  to: string;
  icon: React.FC<{ className?: string }>;
  badge?: number | string;
  badgeVariant?: 'danger' | 'warning' | 'info' | 'success';
}

interface NavGroup {
  heading: string;
  items: NavItem[];
}

// ─── Single nav link ──────────────────────────────────────────────────────────

const SidebarLink: React.FC<{ item: NavItem }> = ({ item }) => {
  const Icon = item.icon;

  return (
    <NavLink
      to={item.to}
      className={({ isActive }) =>
        clsx(
          'group flex items-center gap-2.5 px-3 py-2 rounded-xl text-sm font-medium transition-all duration-150',
          isActive
            ? 'bg-primary-50 text-primary-700'
            : 'text-ink-secondary hover:bg-surface-secondary hover:text-ink',
        )
      }
    >
      {({ isActive }) => (
        <>
          <Icon
            className={clsx(
              'w-4 h-4 flex-shrink-0 transition-colors',
              isActive ? 'text-primary-600' : 'text-ink-muted group-hover:text-ink-secondary',
            )}
          />
          <span className="flex-1 truncate">{item.label}</span>
          {item.badge !== undefined && item.badge !== 0 && (
            <Badge
              variant={item.badgeVariant ?? 'info'}
              size="sm"
              className="ml-auto tabular-nums"
            >
              {item.badge}
            </Badge>
          )}
        </>
      )}
    </NavLink>
  );
};

// ─── Nav group with heading ───────────────────────────────────────────────────

const NavSection: React.FC<{ group: NavGroup }> = ({ group }) => (
  <div className="space-y-0.5">
    <p className="px-3 pt-3 pb-1 text-[10px] font-semibold uppercase tracking-widest text-ink-muted">
      {group.heading}
    </p>
    {group.items.map((item) => (
      <SidebarLink key={item.to} item={item} />
    ))}
  </div>
);

// ─── User profile footer ──────────────────────────────────────────────────────

const UserProfile: React.FC = () => {
  const [open, setOpen] = useState(false);

  return (
    <div className="border-t border-surface-border pt-3 mt-3">
      <button
        onClick={() => setOpen((v) => !v)}
        className="w-full flex items-center gap-2.5 px-3 py-2 rounded-xl hover:bg-surface-secondary transition-colors group"
        aria-expanded={open}
        aria-haspopup="true"
      >
        <Avatar name="BA Reviewer" size="sm" />
        <div className="flex-1 text-left min-w-0">
          <p className="text-sm font-semibold text-ink truncate">BA Reviewer</p>
          <p className="text-[11px] text-ink-muted truncate">Business Analyst</p>
        </div>
        <ChevronDownIcon
          className={clsx(
            'w-4 h-4 text-ink-muted transition-transform duration-200',
            open && 'rotate-180',
          )}
        />
      </button>

      {open && (
        <div className="mt-1 mx-2 bg-white rounded-xl border border-surface-border shadow-card-hover py-1 animate-scale-in">
          <button className="w-full flex items-center gap-2 px-3 py-2 text-sm text-ink-secondary hover:bg-surface-secondary transition-colors">
            <SettingsIcon className="w-4 h-4" />
            Account Settings
          </button>
          <div className="border-t border-surface-border my-1" />
          <button className="w-full flex items-center gap-2 px-3 py-2 text-sm text-status-danger hover:bg-status-dangerBg transition-colors">
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.8}
                d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
            </svg>
            Sign out
          </button>
        </div>
      )}
    </div>
  );
};

// ─── Main Sidebar ─────────────────────────────────────────────────────────────

export const Sidebar: React.FC = () => {
  const { data: summary } = useDashboardSummary();
  const { data: approval } = useApprovalStatus();

  const pendingApprovalCount = summary?.pending_approval ?? 0;
  const inProgressCount      = summary?.in_progress ?? 0;
  const approvalPending      = approval?.status === 'PENDING' ? 1 : 0;

  const navGroups: NavGroup[] = [
    {
      heading: 'Main',
      items: [
        {
          label: 'Dashboard',
          to: '/',
          icon: HomeIcon,
        },
      ],
    },
    {
      heading: 'Project Explorer',
      items: [
        {
          label: 'Projects',
          to: '/projects',
          icon: FolderIcon,
        },
        {
          label: 'Epics & Stories',
          to: '/epics',
          icon: ListIcon,
          badge: summary?.total_stories,
          badgeVariant: 'info',
        },
        {
          label: 'AI Pipeline',
          to: '/pipeline',
          icon: CpuIcon,
          badge: inProgressCount > 0 ? inProgressCount : undefined,
          badgeVariant: 'info',
        },
      ],
    },
    {
      heading: 'Workspace',
      items: [
        {
          label: 'Generation Workspace',
          to: '/workspace',
          icon: WorkspaceIcon,
        },
        {
          label: 'Artifacts',
          to: '/artifacts',
          icon: ArtifactIcon,
          badge: summary?.generated_files,
          badgeVariant: 'info',
        },
        {
          label: 'Traceability',
          to: '/traceability',
          icon: TraceIcon,
        },
      ],
    },
    {
      heading: 'Quality & Approval',
      items: [
        {
          label: 'Validation',
          to: '/validation',
          icon: CheckIcon,
        },
        {
          label: 'Approvals',
          to: '/approvals',
          icon: ApprovalIcon,
          badge: pendingApprovalCount + approvalPending || undefined,
          badgeVariant: 'danger',
        },
        {
          label: 'Reports',
          to: '/reports',
          icon: ReportIcon,
        },
      ],
    },
    {
      heading: 'System',
      items: [
        {
          label: 'Prompt Templates',
          to: '/prompts',
          icon: SettingsIcon,
        },
        {
          label: 'Settings',
          to: '/settings',
          icon: SettingsIcon,
        },
        {
          label: 'Audit Logs',
          to: '/audit',
          icon: AuditIcon,
        },
      ],
    },
  ];

  return (
    <aside className="w-[200px] min-h-screen bg-white border-r border-surface-border flex flex-col flex-shrink-0">
      {/* Logo / Brand */}
      <div className="px-4 py-5 flex items-center gap-3 border-b border-surface-border">
        <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-primary-600 to-primary-400 flex items-center justify-center flex-shrink-0 shadow-sm">
          <span className="text-white font-bold text-sm select-none">BA</span>
        </div>
        <div className="min-w-0">
          <p className="text-sm font-bold text-ink truncate leading-tight">BA Accelerator 2</p>
          <p className="text-[10px] text-ink-muted truncate leading-tight mt-0.5">
            AI Development Orchestrator
          </p>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 overflow-y-auto px-3 py-3 space-y-1 scrollbar-thin">
        {navGroups.map((group) => (
          <NavSection key={group.heading} group={group} />
        ))}
      </nav>

      {/* User profile */}
      <div className="px-3 pb-4">
        <UserProfile />
      </div>
    </aside>
  );
};
