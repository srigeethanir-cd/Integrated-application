import React from 'react';
import { clsx } from 'clsx';

export type ProgressVariant = 'primary' | 'success' | 'warning' | 'danger' | 'purple' | 'orange' | 'teal';

interface ProgressBarProps {
  value: number;           // 0–100
  variant?: ProgressVariant;
  size?: 'xs' | 'sm' | 'md';
  showLabel?: boolean;
  animated?: boolean;
  className?: string;
}

const trackH: Record<NonNullable<ProgressBarProps['size']>, string> = {
  xs: 'h-1',
  sm: 'h-1.5',
  md: 'h-2.5',
};

const fillColor: Record<ProgressVariant, string> = {
  primary: 'bg-primary-500',
  success: 'bg-status-success',
  warning: 'bg-status-warning',
  danger:  'bg-status-danger',
  purple:  'bg-status-purple',
  orange:  'bg-status-orange',
  teal:    'bg-status-teal',
};

export const ProgressBar: React.FC<ProgressBarProps> = ({
  value,
  variant = 'primary',
  size = 'sm',
  showLabel = false,
  animated = true,
  className,
}) => {
  const clamped = Math.min(100, Math.max(0, value));

  return (
    <div className={clsx('w-full', className)}>
      {showLabel && (
        <div className="flex justify-between mb-1">
          <span className="text-xs text-ink-muted">Progress</span>
          <span className="text-xs font-semibold text-ink">{clamped}%</span>
        </div>
      )}
      <div className={clsx('w-full bg-surface-tertiary rounded-full overflow-hidden', trackH[size])}>
        <div
          role="progressbar"
          aria-valuenow={clamped}
          aria-valuemin={0}
          aria-valuemax={100}
          style={{ width: `${clamped}%` }}
          className={clsx(
            'h-full rounded-full',
            fillColor[variant],
            animated && 'transition-all duration-700 ease-out',
          )}
        />
      </div>
    </div>
  );
};
