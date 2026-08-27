import React from 'react';

interface ErrorStateProps {
  message?: string;
  onRetry?: () => void;
}

export const ErrorState: React.FC<ErrorStateProps> = ({
  message = 'Failed to load data.',
  onRetry,
}) => (
  <div className="flex flex-col items-center justify-center py-8 px-4 text-center gap-3">
    {/* Warning icon */}
    <div className="w-10 h-10 rounded-xl bg-status-dangerBg flex items-center justify-center">
      <svg className="w-5 h-5 text-status-danger" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
          d="M12 9v2m0 4h.01M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z" />
      </svg>
    </div>
    <p className="text-sm font-medium text-status-danger">{message}</p>
    {onRetry && (
      <button
        onClick={onRetry}
        className="text-xs font-medium text-primary-600 hover:text-primary-700 transition-colors"
      >
        Try again
      </button>
    )}
  </div>
);
