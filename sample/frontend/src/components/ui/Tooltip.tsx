import React, { useState } from 'react';
import { clsx } from 'clsx';

interface TooltipProps {
  content: string;
  children: React.ReactElement;
  placement?: 'top' | 'bottom';
}

export const Tooltip: React.FC<TooltipProps> = ({ content, children, placement = 'top' }) => {
  const [visible, setVisible] = useState(false);

  return (
    <div
      className="relative inline-flex"
      onMouseEnter={() => setVisible(true)}
      onMouseLeave={() => setVisible(false)}
      onFocus={() => setVisible(true)}
      onBlur={() => setVisible(false)}
    >
      {children}
      {visible && (
        <div
          role="tooltip"
          className={clsx(
            'absolute z-50 px-2 py-1 text-xs font-medium text-white bg-ink rounded-lg whitespace-nowrap',
            'shadow-lg pointer-events-none',
            placement === 'top'
              ? 'bottom-full left-1/2 -translate-x-1/2 mb-1.5'
              : 'top-full left-1/2 -translate-x-1/2 mt-1.5',
          )}
        >
          {content}
          <div
            className={clsx(
              'absolute left-1/2 -translate-x-1/2 w-2 h-2 bg-ink rotate-45',
              placement === 'top' ? 'top-full -mt-1' : 'bottom-full mb-[-4px]',
            )}
          />
        </div>
      )}
    </div>
  );
};
