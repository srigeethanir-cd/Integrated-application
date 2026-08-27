import React from 'react';
import { clsx } from 'clsx';

export type ButtonVariant = 'primary' | 'secondary' | 'ghost' | 'danger';
export type ButtonSize = 'sm' | 'md' | 'lg';

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant;
  size?: ButtonSize;
  loading?: boolean;
  icon?: React.ReactNode;
  iconRight?: React.ReactNode;
}

const variantCls: Record<ButtonVariant, string> = {
  primary:
    'bg-primary-600 text-white hover:bg-primary-700 active:bg-primary-800 shadow-sm',
  secondary:
    'bg-white text-ink border border-surface-border hover:bg-surface-secondary active:bg-surface-tertiary shadow-sm',
  ghost:
    'text-ink-secondary hover:bg-surface-tertiary hover:text-ink active:bg-surface-border',
  danger:
    'bg-status-danger text-white hover:bg-red-600 active:bg-red-700 shadow-sm',
};

const sizeCls: Record<ButtonSize, string> = {
  sm: 'px-3 py-1.5 text-xs gap-1.5',
  md: 'px-4 py-2 text-sm gap-2',
  lg: 'px-5 py-2.5 text-sm gap-2',
};

export const Button: React.FC<ButtonProps> = ({
  variant = 'primary',
  size = 'md',
  loading = false,
  icon,
  iconRight,
  children,
  disabled,
  className,
  ...rest
}) => (
  <button
    {...rest}
    disabled={disabled || loading}
    className={clsx(
      'inline-flex items-center justify-center font-medium rounded-xl',
      'transition-all duration-150 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary-400',
      'disabled:opacity-50 disabled:cursor-not-allowed',
      variantCls[variant],
      sizeCls[size],
      className,
    )}
  >
    {loading ? (
      <svg className="w-4 h-4 animate-spin" viewBox="0 0 24 24" fill="none">
        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
        <path className="opacity-75" fill="currentColor"
          d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
      </svg>
    ) : icon}
    {children}
    {!loading && iconRight}
  </button>
);
