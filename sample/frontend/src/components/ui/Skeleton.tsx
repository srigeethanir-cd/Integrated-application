import React from 'react';
import { clsx } from 'clsx';

interface SkeletonProps {
  className?: string;
  rounded?: 'sm' | 'md' | 'lg' | 'full';
}

export const Skeleton: React.FC<SkeletonProps> = ({ className, rounded = 'md' }) => {
  const roundedMap = {
    sm:   'rounded',
    md:   'rounded-lg',
    lg:   'rounded-xl',
    full: 'rounded-full',
  };

  return (
    <div
      className={clsx(
        'bg-gradient-to-r from-slate-100 via-slate-200 to-slate-100',
        'bg-[length:200%_100%] animate-shimmer',
        roundedMap[rounded],
        className,
      )}
      aria-hidden="true"
    />
  );
};

// ─── Pre-built skeleton layouts ───────────────────────────────────────────────

export const MetricCardSkeleton: React.FC = () => (
  <div className="bg-white rounded-2xl border border-surface-border shadow-card p-5 space-y-3">
    <div className="flex items-center gap-3">
      <Skeleton className="w-10 h-10" rounded="lg" />
      <div className="flex-1 space-y-2">
        <Skeleton className="h-6 w-16" />
        <Skeleton className="h-3 w-24" />
      </div>
    </div>
    <Skeleton className="h-3 w-20" />
  </div>
);

export const EpicCardSkeleton: React.FC = () => (
  <div className="bg-white rounded-2xl border border-surface-border shadow-card p-5 space-y-4 min-w-[220px]">
    <div className="flex items-start justify-between">
      <Skeleton className="w-10 h-10" rounded="lg" />
      <Skeleton className="w-14 h-14" rounded="full" />
    </div>
    <div className="space-y-2">
      <Skeleton className="h-4 w-3/4" />
      <Skeleton className="h-3 w-full" />
      <Skeleton className="h-3 w-4/5" />
    </div>
    <Skeleton className="h-1.5 w-full" rounded="full" />
    <div className="flex justify-between">
      <Skeleton className="h-8 w-16" />
      <Skeleton className="h-8 w-16" />
      <Skeleton className="h-8 w-16" />
    </div>
    <Skeleton className="h-7 w-full" rounded="lg" />
  </div>
);

export const ActivityItemSkeleton: React.FC = () => (
  <div className="flex items-start gap-3">
    <Skeleton className="w-8 h-8 flex-shrink-0" rounded="full" />
    <div className="flex-1 space-y-1.5">
      <Skeleton className="h-3.5 w-3/4" />
      <Skeleton className="h-3 w-1/2" />
      <Skeleton className="h-3 w-16" />
    </div>
  </div>
);

export const HeroBannerSkeleton: React.FC = () => (
  <div className="bg-white rounded-2xl border border-surface-border shadow-card p-6">
    <div className="grid grid-cols-2 gap-6">
      <div className="space-y-4">
        <Skeleton className="h-3 w-28" />
        <Skeleton className="h-8 w-2/3" />
        <Skeleton className="h-3 w-48" />
        <div className="flex gap-2">
          <Skeleton className="h-7 w-24" rounded="full" />
          <Skeleton className="h-7 w-24" rounded="full" />
          <Skeleton className="h-7 w-24" rounded="full" />
        </div>
      </div>
      <div className="space-y-4">
        <Skeleton className="h-3 w-28" />
        <Skeleton className="h-12 w-24" />
        <Skeleton className="h-3 w-full" rounded="full" />
        <Skeleton className="h-3 w-36" />
      </div>
    </div>
  </div>
);
