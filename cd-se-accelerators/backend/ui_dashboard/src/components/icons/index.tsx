/**
 * Inline SVG icon components — no external dependency.
 * All icons are 24×24 viewBox, accepting className prop.
 */

import React from 'react';

interface IconProps {
  className?: string;
  strokeWidth?: number;
}

const icon = (paths: React.ReactNode, props: IconProps = {}) => {
  const { className = 'w-5 h-5', strokeWidth = 1.8 } = props;
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={strokeWidth}>
      {paths}
    </svg>
  );
};

export const HomeIcon      = (p: IconProps) => icon(<path strokeLinecap="round" strokeLinejoin="round" d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" />, p);
export const FolderIcon    = (p: IconProps) => icon(<path strokeLinecap="round" strokeLinejoin="round" d="M3 7a2 2 0 012-2h4l2 2h8a2 2 0 012 2v8a2 2 0 01-2 2H5a2 2 0 01-2-2V7z" />, p);
export const ListIcon      = (p: IconProps) => icon(<path strokeLinecap="round" strokeLinejoin="round" d="M4 6h16M4 10h16M4 14h16M4 18h16" />, p);
export const CpuIcon       = (p: IconProps) => icon(<><rect x="5" y="5" width="14" height="14" rx="2" strokeLinecap="round" strokeLinejoin="round" /><path strokeLinecap="round" strokeLinejoin="round" d="M9 9h6v6H9z" /><path strokeLinecap="round" strokeLinejoin="round" d="M9 1v2M15 1v2M9 21v2M15 21v2M1 9h2M1 15h2M21 9h2M21 15h2" /></>, p);
export const WorkspaceIcon = (p: IconProps) => icon(<path strokeLinecap="round" strokeLinejoin="round" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />, p);
export const ArtifactIcon  = (p: IconProps) => icon(<path strokeLinecap="round" strokeLinejoin="round" d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4" />, p);
export const TraceIcon     = (p: IconProps) => icon(<path strokeLinecap="round" strokeLinejoin="round" d="M9 20l-5.447-2.724A1 1 0 013 16.382V5.618a1 1 0 011.447-.894L9 7m0 13l6-3m-6 3V7m6 10l4.553 2.276A1 1 0 0021 18.382V7.618a1 1 0 00-.553-.894L15 4m0 13V4m0 0L9 7" />, p);
export const CheckIcon     = (p: IconProps) => icon(<path strokeLinecap="round" strokeLinejoin="round" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />, p);
export const ApprovalIcon  = (p: IconProps) => icon(<path strokeLinecap="round" strokeLinejoin="round" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4" />, p);
export const ReportIcon    = (p: IconProps) => icon(<path strokeLinecap="round" strokeLinejoin="round" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />, p);
export const SettingsIcon  = (p: IconProps) => icon(<path strokeLinecap="round" strokeLinejoin="round" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />, p);
export const AuditIcon     = (p: IconProps) => icon(<path strokeLinecap="round" strokeLinejoin="round" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />, p);
export const BellIcon      = (p: IconProps) => icon(<path strokeLinecap="round" strokeLinejoin="round" d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />, p);
export const SearchIcon    = (p: IconProps) => icon(<path strokeLinecap="round" strokeLinejoin="round" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />, p);
export const PlusIcon      = (p: IconProps) => icon(<path strokeLinecap="round" strokeLinejoin="round" d="M12 4v16m8-8H4" />, p);
export const CodeIcon      = (p: IconProps) => icon(<path strokeLinecap="round" strokeLinejoin="round" d="M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4" />, p);
export const PlayIcon      = (p: IconProps) => icon(<path strokeLinecap="round" strokeLinejoin="round" d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z" />, p);
export const DatabaseIcon  = (p: IconProps) => icon(<><ellipse cx="12" cy="5" rx="9" ry="3" strokeLinecap="round" strokeLinejoin="round" /><path strokeLinecap="round" strokeLinejoin="round" d="M21 12c0 1.657-4.03 3-9 3S3 13.657 3 12" /><path strokeLinecap="round" strokeLinejoin="round" d="M3 5v14c0 1.657 4.03 3 9 3s9-1.343 9-3V5" /></>, p);
export const MergeIcon     = (p: IconProps) => icon(<path strokeLinecap="round" strokeLinejoin="round" d="M8 7h12m0 0l-4-4m4 4l-4 4m0 6H4m0 0l4 4m-4-4l4-4" />, p);
export const ClockIcon     = (p: IconProps) => icon(<path strokeLinecap="round" strokeLinejoin="round" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />, p);
export const ChevronDownIcon = (p: IconProps) => icon(<path strokeLinecap="round" strokeLinejoin="round" d="M19 9l-7 7-7-7" />, p);
export const PythonIcon    = (p: IconProps) => icon(<path strokeLinecap="round" strokeLinejoin="round" d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 3c1.66 0 3 .67 3 1.5V9h-6V6.5C9 5.67 10.34 5 12 5zm0 14c-1.66 0-3-.67-3-1.5V15h6v2.5c0 .83-1.34 1.5-3 1.5z" />, p);
export const ReactIcon     = (p: IconProps) => icon(<><circle cx="12" cy="12" r="2.5" /><ellipse cx="12" cy="12" rx="10" ry="4" /><ellipse cx="12" cy="12" rx="10" ry="4" style={{ transform: 'rotate(60deg)', transformOrigin: 'center' }} /><ellipse cx="12" cy="12" rx="10" ry="4" style={{ transform: 'rotate(120deg)', transformOrigin: 'center' }} /></>, p);
export const PostgresIcon  = (p: IconProps) => icon(<path strokeLinecap="round" strokeLinejoin="round" d="M4 7h16M4 11h8m-8 4h5M9 3h6l3 4H6L9 3zM6 11v8a2 2 0 002 2h8a2 2 0 002-2v-8" />, p);
export const ShieldIcon    = (p: IconProps) => icon(<path strokeLinecap="round" strokeLinejoin="round" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />, p);
export const ChartIcon     = (p: IconProps) => icon(<path strokeLinecap="round" strokeLinejoin="round" d="M11 3.055A9.001 9.001 0 1020.945 13H11V3.055z M20.488 9H15V3.512A9.025 9.025 0 0120.488 9z" />, p);
export const UserIcon      = (p: IconProps) => icon(<path strokeLinecap="round" strokeLinejoin="round" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />, p);
export const LogoutIcon    = (p: IconProps) => icon(<path strokeLinecap="round" strokeLinejoin="round" d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />, p);
