/**
 * Coloured icon container used in metric cards and epic cards.
 * Matches the rounded square icon boxes in the design.
 */

import React from 'react';
import { clsx } from 'clsx';

export type IconBoxVariant =
  | 'blue'
  | 'indigo'
  | 'green'
  | 'orange'
  | 'red'
  | 'purple'
  | 'teal'
  | 'yellow';

interface IconBoxProps {
  variant?: IconBoxVariant;
  size?: 'sm' | 'md' | 'lg';
  children: React.ReactNode;
  className?: string;
}

const bg: Record<IconBoxVariant, string> = {
  blue:   'bg-primary-50   text-primary-600',
  indigo: 'bg-indigo-50    text-indigo-600',
  green:  'bg-status-successBg text-status-success',
  orange: 'bg-status-orangeBg  text-status-orange',
  red:    'bg-status-dangerBg  text-status-danger',
  purple: 'bg-status-purpleBg  text-status-purple',
  teal:   'bg-status-tealBg    text-status-teal',
  yellow: 'bg-status-warningBg text-status-warning',
};

const sizes: Record<NonNullable<IconBoxProps['size']>, string> = {
  sm: 'w-8 h-8 rounded-xl',
  md: 'w-10 h-10 rounded-xl',
  lg: 'w-12 h-12 rounded-2xl',
};

export const IconBox: React.FC<IconBoxProps> = ({
  variant = 'blue',
  size = 'md',
  children,
  className,
}) => (
  <div
    className={clsx(
      'flex items-center justify-center flex-shrink-0',
      bg[variant],
      sizes[size],
      className,
    )}
  >
    {children}
  </div>
);
