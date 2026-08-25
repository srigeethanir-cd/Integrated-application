import React from 'react';
import {
  FileText,
  Search,
  BarChart2,
  Box,
  Target,
  Puzzle,
  ClipboardList,
  Edit3,
  ShieldCheck,
  Clock
} from 'lucide-react';

// Custom React Atom SVG Logo Icon
const ReactAtomIcon = ({ className = "w-5 h-5 text-sky-400" }) => (
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
const AngularIcon = ({ className = "w-5 h-5 text-red-500" }) => (
  <svg className={className} viewBox="0 0 250 250" fill="currentColor" xmlns="http://www.w3.org/2000/svg">
    <polygon points="125,30 125,30 125,30 31.9,63.2 46.1,186.3 125,230 203.9,186.3 218.1,63.2" fill="currentColor" opacity="0.9" />
    <polygon points="125,52.1 66.8,182.6 88.7,182.6 100.4,152.5 149.4,152.5 161.1,182.6 183,182.6" fill="white" opacity="0.9" />
  </svg>
);

/**
 * Per-segment connecting line between two adjacent pipeline stages.
 * Renders a gray track with a colored fill whose state is
 * driven entirely by the real backend stage index.
 *
 * segmentStatus:
 *   'completed' → green fill, instant
 *   'active'    → purple animated fill + shimmer
 *   'upcoming'  → gray (no fill)
 */
function SegmentLine({ segmentStatus }) {
  return (
    <div className="flex-1 flex items-center self-stretch px-0.5">
      {/* Track (gray background line) */}
      <div className="w-full h-[3px] rounded-full bg-[#E0E5F2] dark:bg-slate-700 relative overflow-hidden">
        {/* Completed fill — solid green */}
        {segmentStatus === 'completed' && (
          <div className="absolute inset-0 rounded-full bg-[#05CD99] transition-all duration-300" />
        )}

        {/* Active fill — animated purple gradient + shimmer */}
        {segmentStatus === 'active' && (
          <>
            {/* Expanding fill bar */}
            <div
              className="absolute inset-y-0 left-0 w-full rounded-full bg-gradient-to-r from-[#7357FF] to-[#4318FF] origin-left animate-seg-fill animate-seg-pulse"
            />
            {/* Light shimmer sweep */}
            <div
              className="absolute inset-y-0 left-0 w-1/3 rounded-full bg-gradient-to-r from-transparent via-white/30 to-transparent animate-seg-shimmer pointer-events-none"
            />
          </>
        )}
      </div>
    </div>
  );
}

export default function PipelineProgressCard({
  currentStageIndex = -1, // 0 to 8, or 9 for completed
  progressPercent = 0,
  isExecuting = false,
  timerSeconds = 0,
  detectedFramework = null,
  pipelineStatus = 'idle', // 'idle' | 'running' | 'completed' | 'failed'
  failedStageIndex = -1,
}) {
  const stages = [
    { id: 1, name: 'Source Ingestion', icon: FileText },
    { id: 2, name: 'Framework Detection', icon: Search },
    { id: 3, name: 'Analyzer', icon: BarChart2 },
    { id: 4, name: 'IR Generator', icon: Box },
    { id: 5, name: 'Strategy Engine', icon: Target },
    { id: 6, name: 'Edge Case Generator', icon: Puzzle },
    { id: 7, name: 'Test Case Generator', icon: ClipboardList },
    { id: 8, name: 'Test Writer', icon: Edit3 },
    { id: 9, name: 'Validation', icon: ShieldCheck },
  ];

  // Format timer seconds into HH:MM:SS
  const formatTimer = (totalSec) => {
    const hours = String(Math.floor(totalSec / 3600)).padStart(2, '0');
    const mins = String(Math.floor((totalSec % 3600) / 60)).padStart(2, '0');
    const secs = String(totalSec % 60).padStart(2, '0');
    return `${hours}:${mins}:${secs}`;
  };

  /**
   * Derive segment status for the line BEFORE stage at `idx`.
   * Segment i (before stage idx=i, connecting stage i-1 → stage i):
   *   'completed' — if stage at idx is already done (idx < currentStageIndex) or pipeline completed
   *   'active'    — if stage at idx is currently running (idx === currentStageIndex) and pipeline is running
   *   'upcoming'  — otherwise
   */
  const getSegmentStatus = (idx) => {
    if (pipelineStatus === 'completed' || currentStageIndex >= 9) return 'completed';
    if (idx < currentStageIndex) return 'completed';
    if (idx === currentStageIndex && isExecuting && pipelineStatus === 'running') return 'active';
    return 'upcoming';
  };

  return (
    <div className="bg-white dark:bg-[#1B1E3A] rounded-2xl border border-[#E0E5F2] dark:border-slate-800 p-3 sm:p-3.5 shadow-sm transition-colors duration-200">
      {/* Header */}
      <div className="flex items-center justify-between mb-2">
        <div>
          <h2 className="font-bold text-[#1B2559] dark:text-white text-sm sm:text-base">
            Pipeline Progress
          </h2>
          <p className="text-[#707EAE] dark:text-[#A3AED0] text-[11px] font-medium">
            {pipelineStatus === 'completed'
              ? '✔ Pipeline execution completed successfully'
              : pipelineStatus === 'failed'
              ? '✖ Pipeline execution failed'
              : isExecuting
              ? 'Live pipeline execution in progress...'
              : 'Ready to execute 9-stage testing pipeline'}
          </p>
        </div>

        {/* Timer Badge */}
        <div className="bg-[#EAEFFF] dark:bg-[#4318FF]/20 border border-[#D6E4FF] dark:border-[#4318FF]/30 text-[#4318FF] dark:text-[#7357FF] px-2.5 py-0.5 rounded-full text-[11px] font-semibold flex items-center gap-1.5 shadow-xs">
          <Clock className="w-3 h-3 stroke-[2.2]" />
          <span>
            {pipelineStatus === 'completed'
              ? `Execution time: ${formatTimer(timerSeconds)}`
              : pipelineStatus === 'failed'
              ? `Execution failed at: ${formatTimer(timerSeconds)}`
              : `Elapsed time: ${formatTimer(timerSeconds)}`}
          </span>
        </div>
      </div>

      {/* ═══════════════════════════════════════════════════════════ */}
      {/* 9-Step Pipeline — Interleaved Nodes + Segment Lines       */}
      {/* ═══════════════════════════════════════════════════════════ */}
      <div className="relative mb-3 px-1">
        <div className="flex items-start relative z-10">
          {stages.map((stage, idx) => {
            const Icon = stage.icon;

            // Determine exact status per stage
            const isCompleted = (pipelineStatus === 'completed' || currentStageIndex >= 9 || idx < currentStageIndex);
            const isRunning = isExecuting && idx === currentStageIndex && pipelineStatus === 'running';
            const isFailed = (pipelineStatus === 'failed' && (idx === failedStageIndex || idx === currentStageIndex));
            const isFrameworkDetected = idx === 1 && (currentStageIndex >= 1 || pipelineStatus === 'completed') && Boolean(detectedFramework);

            // Segment line status (line leading INTO this node)
            const segStatus = idx > 0 ? getSegmentStatus(idx) : null;

            return (
              <React.Fragment key={stage.id}>
                {/* ── Connecting segment line BEFORE this node ── */}
                {idx > 0 && (
                  <div className="flex-1 flex items-center" style={{ paddingTop: '28px' }}>
                    <SegmentLine segmentStatus={segStatus} />
                  </div>
                )}

                {/* ── Stage Node Column ── */}
                <div className="flex flex-col items-center group relative min-w-[65px]">
                  {/* Step Number Circle Badge */}
                  <div
                    className={`w-4 h-4 sm:w-5 sm:h-5 rounded-full text-[9px] sm:text-[10px] font-bold flex items-center justify-center mb-1 transition-all duration-300 ${
                      isCompleted
                        ? 'bg-[#05CD99] text-white shadow-xs'
                        : isFailed
                        ? 'bg-[#EE5D50] text-white shadow-xs'
                        : isRunning
                        ? 'bg-[#4318FF] text-white animate-pulse shadow-md shadow-[#4318FF]/30'
                        : 'bg-[#E0E5F2] dark:bg-slate-700 text-[#707EAE] dark:text-slate-300'
                    }`}
                  >
                    {stage.id}
                  </div>

                  {/* Node Icon Circle */}
                  <div
                    className={`w-10 h-10 sm:w-11 sm:h-11 rounded-full flex items-center justify-center transition-all duration-300 ${
                      isCompleted
                        ? 'border-2 border-[#05CD99] bg-[#E6F9F0] dark:bg-[#1B1E3A] text-[#05CD99] shadow-xs'
                        : isFailed
                        ? 'border-2 border-[#EE5D50] bg-[#FDEDEC] dark:bg-[#EE5D50]/20 text-[#EE5D50] shadow-xs'
                        : isRunning
                        ? 'border-2 border-[#4318FF] bg-[#EAEFFF] dark:bg-[#4318FF]/30 text-[#4318FF] dark:text-[#7357FF] animate-pulse ring-4 ring-[#7357FF]/20'
                        : 'border-2 border-[#E0E5F2] dark:border-slate-700 bg-white dark:bg-[#1B1E3A] text-[#A3AED0] dark:text-slate-500'
                    }`}
                  >
                    <Icon className="w-4 h-4 sm:w-4.5 sm:h-4.5 stroke-[2]" />
                  </div>

                  {/* Stage Title */}
                  <span
                    className={`text-[10px] sm:text-[11px] font-semibold text-center mt-1.5 max-w-[78px] leading-tight transition-colors ${
                      isCompleted
                        ? 'text-[#05CD99] dark:text-[#05CD99] font-bold'
                        : isFailed
                        ? 'text-[#EE5D50] font-bold'
                        : isRunning
                        ? 'text-[#4318FF] dark:text-[#7357FF] font-bold'
                        : 'text-[#707EAE] dark:text-[#A3AED0] font-medium'
                    }`}
                  >
                    {stage.name}
                  </span>

                  {/* Checkmark Status Badge below title */}
                  <div className="mt-1 flex flex-col items-center">
                    {isCompleted ? (
                      <div className="w-3.5 h-3.5 rounded-full bg-[#05CD99] text-white flex items-center justify-center shadow-xs">
                        <svg
                          className="w-2.5 h-2.5 stroke-[3]"
                          fill="none"
                          viewBox="0 0 24 24"
                          stroke="currentColor"
                        >
                          <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            d="M5 13l4 4L19 7"
                          />
                        </svg>
                      </div>
                    ) : isFailed ? (
                      <div className="w-3.5 h-3.5 rounded-full bg-[#EE5D50] text-white flex items-center justify-center shadow-xs text-[9px] font-bold">
                        ✕
                      </div>
                    ) : isRunning ? (
                      <div className="w-3.5 h-3.5 rounded-full border-2 border-[#4318FF] border-t-transparent animate-spin"></div>
                    ) : (
                      <div className="w-3.5 h-3.5 rounded-full border-2 border-[#E0E5F2] dark:border-slate-700 bg-white dark:bg-[#1B1E3A]"></div>
                    )}

                    {/* Stage 2 Specific: Framework Detected Badge */}
                    {isFrameworkDetected && (
                      <div className="mt-1 flex flex-col items-center animate-fade-in">
                        {(detectedFramework || '').toLowerCase() === 'angular' ? (
                          <AngularIcon className="w-5 h-5 text-red-500" />
                        ) : (
                          <ReactAtomIcon className="w-5 h-5 text-[#7357FF]" />
                        )}
                        <span className="text-[9px] font-bold text-[#4318FF] dark:text-[#7357FF] tracking-tight whitespace-nowrap">
                          {detectedFramework}
                        </span>
                      </div>
                    )}
                  </div>
                </div>
              </React.Fragment>
            );
          })}
        </div>
      </div>

      {/* Progress Bar with Percentage */}
      <div className="flex items-center gap-3 px-1">
        <div className="flex-1 bg-[#F4F7FE] dark:bg-slate-800 rounded-full h-2 overflow-hidden p-0.5 border border-[#E0E5F2] dark:border-slate-700/50">
          <div
            className={`h-full rounded-full bg-gradient-to-r from-[#7357FF] to-[#4318FF] transition-all duration-300 ease-out relative ${
              isExecuting ? 'progress-striped animate-stripe' : ''
            }`}
            style={{ width: `${pipelineStatus === 'completed' ? 100 : progressPercent}%` }}
          ></div>
        </div>
        <span className="text-xs font-bold text-[#4318FF] dark:text-[#7357FF] min-w-[36px] text-right">
          {pipelineStatus === 'completed' ? 100 : progressPercent}%
        </span>
      </div>
    </div>
  );
}
