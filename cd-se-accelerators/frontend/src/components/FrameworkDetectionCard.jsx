import React from 'react';
import { CheckCircle, Layers, Zap } from 'lucide-react';

// React Atom SVG Icon
const ReactAtomIcon = ({ className = "w-8 h-8" }) => (
  <svg className={className} viewBox="-11.5 -10.23174 23 20.46348" fill="none" xmlns="http://www.w3.org/2000/svg">
    <circle cx="0" cy="0" r="2.05" fill="currentColor" />
    <g stroke="currentColor" strokeWidth="1" fill="none">
      <ellipse rx="11" ry="4.2" />
      <ellipse rx="11" ry="4.2" transform="rotate(60)" />
      <ellipse rx="11" ry="4.2" transform="rotate(120)" />
    </g>
  </svg>
);

// Angular Shield SVG Icon
const AngularIcon = ({ className = "w-8 h-8" }) => (
  <svg className={className} viewBox="0 0 250 250" fill="currentColor" xmlns="http://www.w3.org/2000/svg">
    <polygon points="125,30 125,30 125,30 31.9,63.2 46.1,186.3 125,230 203.9,186.3 218.1,63.2" fill="currentColor" opacity="0.9" />
    <polygon points="125,52.1 66.8,182.6 88.7,182.6 100.4,152.5 149.4,152.5 161.1,182.6 183,182.6" fill="white" opacity="0.9" />
    <polygon points="125,52.1 125,182.6 149.4,152.5 100.4,152.5" fill="white" opacity="0.5" />
    <polygon points="125,52.1 149.4,152.5 125,120 100.4,152.5" fill="white" opacity="0.3" />
  </svg>
);

// Next.js Icon
const NextjsIcon = ({ className = "w-8 h-8" }) => (
  <svg className={className} viewBox="0 0 180 180" fill="none" xmlns="http://www.w3.org/2000/svg">
    <mask id="mask0" maskUnits="userSpaceOnUse" x="0" y="0" width="180" height="180">
      <circle cx="90" cy="90" r="90" fill="white" />
    </mask>
    <g mask="url(#mask0)">
      <circle cx="90" cy="90" r="90" fill="black" />
      <path d="M149.508 157.52L69.142 54H54V125.97H66.1765V69.3836L139.999 164.845C143.333 162.614 146.509 160.165 149.508 157.52Z" fill="url(#paint0)" />
      <rect x="115" y="54" width="12" height="72" fill="url(#paint1)" />
    </g>
    <defs>
      <linearGradient id="paint0" x1="109" y1="116.5" x2="144.5" y2="160.5" gradientUnits="userSpaceOnUse">
        <stop stopColor="white" />
        <stop offset="1" stopColor="white" stopOpacity="0" />
      </linearGradient>
      <linearGradient id="paint1" x1="121" y1="54" x2="120.799" y2="106.875" gradientUnits="userSpaceOnUse">
        <stop stopColor="white" />
        <stop offset="1" stopColor="white" stopOpacity="0" />
      </linearGradient>
    </defs>
  </svg>
);

// Vue icon fallback
const VueIcon = ({ className = "w-8 h-8" }) => (
  <svg className={className} viewBox="0 0 261.76 226.69" xmlns="http://www.w3.org/2000/svg">
    <path d="m161.096.001l-30.225 52.351L100.647.001H-.005l130.877 226.688L261.749.001z" fill="#41b883"/>
    <path d="m161.096.001l-30.225 52.351L100.647.001H52.346l78.526 136.01L209.398.001z" fill="#34495e"/>
  </svg>
);

const FRAMEWORK_CONFIG = {
  React: {
    Icon: ReactAtomIcon,
    color: 'brand',
    iconColor: 'text-[#7357FF]',
    bgColor: 'bg-[#F4F7FE] dark:bg-[#1B1E3A]/60',
    borderColor: 'border-[#E0E5F2] dark:border-[#4318FF]/40',
    tagColor: 'bg-[#EAEFFF] dark:bg-[#4318FF]/30 text-[#4318FF] dark:text-[#7357FF]',
    glowColor: 'shadow-[#4318FF]/20',
    badgeText: 'Supported',
    defaultVersion: '18.2.0',
  },
  Angular: {
    Icon: AngularIcon,
    color: 'red',
    iconColor: 'text-red-500',
    bgColor: 'bg-red-50 dark:bg-red-950/30',
    borderColor: 'border-red-200 dark:border-red-900/40',
    tagColor: 'bg-red-100 dark:bg-red-950/50 text-red-600 dark:text-red-400',
    glowColor: 'shadow-red-500/20',
    badgeText: 'Supported',
    defaultVersion: '17.0.0',
  },
  'Next.js': {
    Icon: NextjsIcon,
    color: 'slate',
    iconColor: 'text-slate-900 dark:text-white',
    bgColor: 'bg-slate-50 dark:bg-slate-800/60',
    borderColor: 'border-slate-200 dark:border-slate-700',
    tagColor: 'bg-slate-200 dark:bg-slate-700 text-slate-700 dark:text-slate-300',
    glowColor: 'shadow-slate-500/20',
    badgeText: 'Supported',
    defaultVersion: '14.0.0',
  },
  Vue: {
    Icon: VueIcon,
    color: 'emerald',
    iconColor: 'text-emerald-500',
    bgColor: 'bg-emerald-50 dark:bg-emerald-950/30',
    borderColor: 'border-emerald-200 dark:border-emerald-900/40',
    tagColor: 'bg-emerald-100 dark:bg-emerald-950/50 text-emerald-600 dark:text-emerald-400',
    glowColor: 'shadow-emerald-500/20',
    badgeText: 'Supported',
    defaultVersion: '3.0.0',
  },
};

export default function FrameworkDetectionCard({
  framework = 'React',
  version = null,
  confidence = 100,
  reason = '',
}) {
  const config = FRAMEWORK_CONFIG[framework] || FRAMEWORK_CONFIG['React'];
  const { Icon, iconColor, bgColor, borderColor, tagColor, glowColor, badgeText, defaultVersion } = config;
  const displayVersion = version || config.defaultVersion;

  return (
    <div
      className={`rounded-2xl border ${borderColor} ${bgColor} p-4 sm:p-5 shadow-lg ${glowColor} transition-all duration-500 animate-fade-in`}
      role="region"
      aria-label={`Framework Detection Result: ${framework}`}
    >
      {/* Card Header */}
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <div className="w-7 h-7 rounded-lg bg-emerald-500 text-white flex items-center justify-center shadow-sm">
            <CheckCircle className="w-4 h-4 stroke-[2.5]" />
          </div>
          <div>
            <p className="text-[10px] font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-widest">
              Stage 2 — Framework Detection
            </p>
            <p className="text-[11px] font-bold text-emerald-600 dark:text-emerald-400">
              Detection Successful
            </p>
          </div>
        </div>

        {/* Confidence Pill */}
        <div className="flex items-center gap-1.5 bg-white/70 dark:bg-slate-900/60 border border-slate-200 dark:border-slate-700/60 rounded-full px-2.5 py-1">
          <Zap className="w-3 h-3 text-amber-500" />
          <span className="text-[10px] font-bold text-slate-600 dark:text-slate-300">
            {confidence}% confidence
          </span>
        </div>
      </div>

      {/* Main Detection Result Row */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center gap-4 bg-white/70 dark:bg-slate-900/50 border border-white/80 dark:border-slate-700/50 rounded-xl p-3.5 shadow-xs backdrop-blur-sm">
        {/* Framework Icon */}
        <div className={`w-14 h-14 rounded-2xl bg-white dark:bg-slate-800 border ${borderColor} flex items-center justify-center shrink-0 shadow-sm`}>
          <Icon className={`w-9 h-9 ${iconColor}`} />
        </div>

        {/* Framework Details */}
        <div className="flex-1 min-w-0">
          <div className="flex flex-wrap items-center gap-2 mb-1">
            <h3 className="text-lg sm:text-xl font-extrabold text-slate-900 dark:text-white tracking-tight">
              {framework}
            </h3>
            <span className={`text-[10px] font-bold px-2.5 py-0.5 rounded-full ${tagColor} border ${borderColor}`}>
              {badgeText}
            </span>
          </div>

          <div className="flex flex-wrap items-center gap-3">
            {/* Version badge */}
            <div className="flex items-center gap-1.5">
              <Layers className="w-3 h-3 text-slate-400" />
              <span className="text-xs font-semibold text-slate-500 dark:text-slate-400">
                Version: <span className="text-slate-700 dark:text-slate-200 font-bold">{displayVersion}</span>
              </span>
            </div>

            {/* Divider */}
            <div className="h-3 w-px bg-slate-300 dark:bg-slate-700 hidden sm:block" />

            {/* Reason text */}
            {reason && (
              <p className="text-[11px] text-slate-500 dark:text-slate-400 leading-tight max-w-sm truncate" title={reason}>
                {reason}
              </p>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
