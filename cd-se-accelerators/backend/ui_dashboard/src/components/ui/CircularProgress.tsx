import React from 'react';
import { clsx } from 'clsx';

export type CircularVariant = 'primary' | 'success' | 'warning' | 'danger' | 'purple' | 'orange' | 'teal';

interface CircularProgressProps {
  value: number;            // 0–100
  size?: number;            // px — default 64
  strokeWidth?: number;     // default 5
  variant?: CircularVariant;
  label?: React.ReactNode;  // centre text (defaults to value%)
  className?: string;
}

const strokeColors: Record<CircularVariant, string> = {
  primary: '#3b82f6',
  success: '#22c55e',
  warning: '#f59e0b',
  danger:  '#ef4444',
  purple:  '#8b5cf6',
  orange:  '#f97316',
  teal:    '#14b8a6',
};

export const CircularProgress: React.FC<CircularProgressProps> = ({
  value,
  size = 64,
  strokeWidth = 5,
  variant = 'primary',
  label,
  className,
}) => {
  const clamped = Math.min(100, Math.max(0, value));
  const radius  = (size - strokeWidth * 2) / 2;
  const cx      = size / 2;
  const cy      = size / 2;
  const circumference = 2 * Math.PI * radius;
  const dashOffset    = circumference - (clamped / 100) * circumference;
  const color         = strokeColors[variant];

  return (
    <div
      className={clsx('relative inline-flex items-center justify-center flex-shrink-0', className)}
      style={{ width: size, height: size }}
    >
      <svg
        width={size}
        height={size}
        viewBox={`0 0 ${size} ${size}`}
        fill="none"
        aria-hidden="true"
        style={{ transform: 'rotate(-90deg)' }}
      >
        {/* Track */}
        <circle
          cx={cx}
          cy={cy}
          r={radius}
          stroke="#e2e8f0"
          strokeWidth={strokeWidth}
        />
        {/* Progress arc */}
        <circle
          cx={cx}
          cy={cy}
          r={radius}
          stroke={color}
          strokeWidth={strokeWidth}
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={dashOffset}
          style={{ transition: 'stroke-dashoffset 0.8s ease-out' }}
        />
      </svg>
      {/* Centre label */}
      <div className="absolute inset-0 flex items-center justify-center">
        <span className="text-[11px] font-bold text-ink leading-none">
          {label ?? `${clamped}%`}
        </span>
      </div>
    </div>
  );
};
