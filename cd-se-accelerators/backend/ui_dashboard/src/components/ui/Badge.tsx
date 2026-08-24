import React from 'react';
import { clsx } from 'clsx';

export type BadgeVariant =
  | 'success'
  | 'warning'
  | 'danger'
  | 'info'
  | 'purple'
  | 'orange'
  | 'teal'
  | 'neutral'
  | 'active';

export type BadgeSize = 'sm' | 'md';

interface BadgeProps {
  variant?: BadgeVariant;
  size?: BadgeSize;
  dot?: boolean;
  children: React.ReactNode;
  className?: string;
}

const variantStyles: Record<BadgeVariant, string> = {
  success: 'bg-status-successBg text-status-success',
  warning: 'bg-status-warningBg text-status-warning',
  danger:  'bg-status-dangerBg  text-status-danger',
  info:    'bg-status-infoBg    text-status-info',
  purple:  'bg-status-purpleBg  text-status-purple',
  orange:  'bg-status-orangeBg  text-status-orange',
  teal:    'bg-status-tealBg    text-status-teal',
  neutral: 'bg-surface-tertiary text-ink-secondary',
  active:  'bg-primary-50       text-primary-600',
};

const dotColors: Record<BadgeVariant, string> = {
  success: 'bg-status-success',
  warning: 'bg-status-warning',
  danger:  'bg-status-danger',
  info:    'bg-status-info',
  purple:  'bg-status-purple',
  orange:  'bg-status-orange',
  teal:    'bg-status-teal',
  neutral: 'bg-ink-muted',
  active:  'bg-primary-500',
};

const sizeStyles: Record<BadgeSize, string> = {
  sm: 'px-2 py-0.5 text-[11px] gap-1',
  md: 'px-2.5 py-1 text-xs gap-1.5',
};

export const Badge: React.FC<BadgeProps> = ({
  variant = 'neutral',
  size = 'md',
  dot = false,
  children,
  className,
}) => (
  <span
    className={clsx(
      'inline-flex items-center font-medium rounded-full whitespace-nowrap',
      variantStyles[variant],
      sizeStyles[size],
      className,
    )}
  >
    {dot && (
      <span className={clsx('rounded-full flex-shrink-0 w-1.5 h-1.5', dotColors[variant])} />
    )}
    {children}
  </span>
);

// ─── Status → variant mapper (used by many components) ───────────────────────

export function statusToBadgeVariant(status: string): BadgeVariant {
  const s = status?.toUpperCase() ?? '';
  if (['MERGED', 'COMPLETED', 'VALIDATED', 'PASSED', 'APPROVED', 'GENERATED'].includes(s))
    return 'success';
  if (['GENERATING', 'RUNNING', 'IN_PROGRESS', 'RUNNING_STAGE_1', 'RUNNING_STAGE_2'].includes(s))
    return 'info';
  if (['PAUSED_FOR_HUMAN_APPROVAL', 'PAUSED_FOR_FINAL_APPROVAL', 'PENDING', 'PREVIEW_READY'].includes(s))
    return 'warning';
  if (['FAILED', 'REJECTED', 'VALIDATION_FAILED', 'REJECTED_BY_BA'].includes(s))
    return 'danger';
  if (['EXPORT_READY', 'READY_TO_MERGE'].includes(s)) return 'teal';
  if (s === 'ACTIVE') return 'active';
  return 'neutral';
}
