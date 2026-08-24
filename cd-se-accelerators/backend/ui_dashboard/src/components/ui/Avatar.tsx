import React from 'react';
import { clsx } from 'clsx';

interface AvatarProps {
  name: string;
  size?: 'xs' | 'sm' | 'md' | 'lg';
  src?: string;
  className?: string;
}

const sizeCls: Record<NonNullable<AvatarProps['size']>, string> = {
  xs: 'w-6 h-6 text-[10px]',
  sm: 'w-8 h-8 text-xs',
  md: 'w-9 h-9 text-sm',
  lg: 'w-11 h-11 text-base',
};

// Deterministic colour from name
const COLOURS = [
  'bg-primary-500',
  'bg-status-purple',
  'bg-status-teal',
  'bg-status-orange',
  'bg-status-success',
  'bg-status-warning',
];

function colourFor(name: string): string {
  let hash = 0;
  for (let i = 0; i < name.length; i++) hash = name.charCodeAt(i) + ((hash << 5) - hash);
  return COLOURS[Math.abs(hash) % COLOURS.length];
}

function initials(name: string): string {
  return name
    .split(' ')
    .filter(Boolean)
    .slice(0, 2)
    .map((w) => w[0].toUpperCase())
    .join('');
}

export const Avatar: React.FC<AvatarProps> = ({ name, size = 'md', src, className }) => {
  if (src) {
    return (
      <img
        src={src}
        alt={name}
        className={clsx('rounded-full object-cover flex-shrink-0', sizeCls[size], className)}
      />
    );
  }

  return (
    <div
      className={clsx(
        'rounded-full flex items-center justify-center font-semibold text-white flex-shrink-0',
        sizeCls[size],
        colourFor(name),
        className,
      )}
      aria-label={name}
    >
      {initials(name)}
    </div>
  );
};
