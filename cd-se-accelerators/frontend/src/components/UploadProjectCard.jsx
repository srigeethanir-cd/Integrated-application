import React, { useRef, useState } from 'react';
import {
  Folder,
  Play,
  FileCode2,
  FileText,
  Code2,
  Image as ImageIcon,
  Search,
  Check,
  Plus,
  Sparkles,
  ArrowUp,
  UploadCloud,
  ScanLine,
  Braces,
  DatabaseZap,
  GitMerge,
  Loader2,
  Box,
  Lightbulb,
  Layers,
  CheckCircle2,
  ArrowRight,
  Cpu,
  LayoutGrid,
  Sliders,
  Anchor,
  Webhook,
  Route
} from 'lucide-react';

// Custom React Atom SVG Logo Icon
const ReactAtomIcon = ({ className = "w-8 h-8 text-sky-400" }) => (
  <svg className={className} viewBox="-11.5 -10.23174 23 20.46348" fill="none" xmlns="http://www.w3.org/2000/svg">
    <circle cx="0" cy="0" r="2.05" fill="currentColor" />
    <g stroke="currentColor" strokeWidth="1" fill="none">
      <ellipse rx="11" ry="4.2" />
      <ellipse rx="11" ry="4.2" transform="rotate(60)" />
      <ellipse rx="11" ry="4.2" transform="rotate(120)" />
    </g>
  </svg>
);

// Analyzer sub-step progress strip (4 steps)
const ANALYZER_STEPS = [
  { label: 'Scanning Files',           sub: 'Reading project files',      Icon: ScanLine },
  { label: 'Parsing Code',             sub: 'Understanding structure',    Icon: Braces },
  { label: 'Extracting Metadata',      sub: 'Collecting useful info',     Icon: DatabaseZap },
  { label: 'Building Dependency Graph',sub: 'Mapping relationships',      Icon: GitMerge },
];

function AnalyzerSubStepsBar({ activeSubStep }) {
  // activeSubStep: 0-3 = in-progress step, steps before it are done
  return (
    <div className="w-full max-w-3xl flex items-center justify-center gap-0 my-2 select-none">
      {ANALYZER_STEPS.map((step, i) => {
        const isDone    = i < activeSubStep;
        const isActive  = i === activeSubStep;
        const isPending = i > activeSubStep;
        const Icon = step.Icon;

        return (
          <React.Fragment key={i}>
            {/* Step node */}
            <div className="flex flex-col items-center gap-1.5 min-w-[110px]">
              {/* Icon bubble */}
              <div
                className={`w-10 h-10 rounded-full flex items-center justify-center border-2 transition-all duration-500 ${
                  isDone
                    ? 'bg-emerald-500 border-emerald-500 text-white shadow-sm shadow-emerald-400/30'
                    : isActive
                    ? 'bg-white dark:bg-slate-800 border-sky-400 text-sky-500 shadow-md shadow-sky-400/25 ring-4 ring-sky-100 dark:ring-sky-950/40'
                    : 'bg-slate-50 dark:bg-slate-800/60 border-slate-200 dark:border-slate-700 text-slate-300 dark:text-slate-600'
                }`}
              >
                {isDone ? (
                  <Check className="w-5 h-5 stroke-[3]" />
                ) : isActive ? (
                  <Loader2 className="w-5 h-5 animate-spin" />
                ) : (
                  <Icon className="w-4.5 h-4.5" />
                )}
              </div>

              {/* Label */}
              <div className="text-center">
                <p
                  className={`text-[11px] font-bold leading-tight transition-colors duration-300 ${
                    isDone
                      ? 'text-emerald-600 dark:text-emerald-400'
                      : isActive
                      ? 'text-sky-600 dark:text-sky-400'
                      : 'text-slate-400 dark:text-slate-600'
                  }`}
                >
                  {step.label}
                </p>
                <p
                  className={`text-[10px] leading-tight mt-0.5 transition-colors duration-300 ${
                    isActive ? 'text-slate-500 dark:text-slate-400' : 'text-slate-300 dark:text-slate-600'
                  }`}
                >
                  {step.sub}
                </p>
              </div>
            </div>

            {/* Connector arrow between steps */}
            {i < ANALYZER_STEPS.length - 1 && (
              <div className="flex items-center justify-center mt-[-16px] mx-1">
                <div
                  className={`h-0.5 w-8 rounded-full transition-colors duration-500 ${
                    i < activeSubStep
                      ? 'bg-emerald-400'
                      : 'bg-slate-200 dark:bg-slate-700'
                  }`}
                />
                <svg
                  className={`w-3 h-3 -ml-0.5 transition-colors duration-500 ${
                    i < activeSubStep ? 'text-emerald-400' : 'text-slate-300 dark:text-slate-600'
                  }`}
                  viewBox="0 0 12 12"
                  fill="currentColor"
                >
                  <path d="M4 2l4 4-4 4" stroke="currentColor" strokeWidth="1.5" fill="none" strokeLinecap="round" strokeLinejoin="round" />
                </svg>
              </div>
            )}
          </React.Fragment>
        );
      })}
    </div>
  );
}

// IR Generator 3-step progress view
const IR_STEPS = [
  {
    label: 'Collecting Insights',
    sub: 'Gathering component structure,\nUI elements, states, and interactions.',
    icon: (
      <svg viewBox="0 0 48 48" className="w-10 h-10" fill="none">
        <rect x="6" y="10" width="36" height="28" rx="4" fill="#e0f2fe" stroke="#7dd3fc" strokeWidth="2"/>
        <rect x="11" y="17" width="26" height="3" rx="1.5" fill="#38bdf8"/>
        <rect x="11" y="23" width="20" height="3" rx="1.5" fill="#38bdf8" opacity="0.6"/>
        <rect x="11" y="29" width="14" height="3" rx="1.5" fill="#38bdf8" opacity="0.3"/>
      </svg>
    ),
  },
  {
    label: 'Building IR Model',
    sub: 'Structuring relationships between\ncomponents, elements and behaviors.',
    icon: (
      <svg viewBox="0 0 48 48" className="w-10 h-10" fill="none">
        <rect x="10" y="10" width="28" height="28" rx="6" fill="#dbeafe" stroke="#60a5fa" strokeWidth="2"/>
        <polygon points="24,14 30,24 24,34 18,24" fill="#3b82f6" opacity="0.85"/>
        <circle cx="24" cy="24" r="4" fill="white"/>
      </svg>
    ),
  },
  {
    label: 'Finalizing IR',
    sub: 'Validating and optimizing the IR for\naccurate test case generation.',
    icon: (
      <svg viewBox="0 0 48 48" className="w-10 h-10" fill="none">
        <rect x="8" y="8" width="32" height="32" rx="6" fill="#dcfce7" stroke="#4ade80" strokeWidth="2"/>
        <path d="M15 24 l7 7 l11-13" stroke="#16a34a" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round" fill="none"/>
      </svg>
    ),
  },
];

function IRGeneratorView({ irSubStep, irStats }) {
  // irSubStep: -1 = idle, 0=Collecting, 1=Building, 2=Finalizing
  const active = irSubStep >= 0 ? irSubStep : 2;
  const isComplete = irSubStep === -1;

  const stepStatus = (i) => {
    if (isComplete) return 'done';
    if (i < active) return 'done';
    if (i === active) return 'active';
    return 'pending';
  };

  return (
    <div className="w-full flex flex-col gap-3 py-1">
      {/* ---- Three-step visual strip ---- */}
      <div className="flex items-stretch gap-3 justify-center flex-wrap sm:flex-nowrap">
        {IR_STEPS.map((step, i) => {
          const status = stepStatus(i);
          const isDone    = status === 'done';
          const isActive  = status === 'active';
          const isPending = status === 'pending';

          return (
            <React.Fragment key={i}>
              <div
                className={`relative flex flex-col items-center gap-2 rounded-2xl border p-4 sm:p-5 flex-1 min-w-[130px] transition-all duration-500 ${
                  isActive
                    ? 'border-sky-300 bg-sky-50/80 dark:bg-sky-950/30 shadow-md shadow-sky-400/15'
                    : isDone
                    ? 'border-emerald-200 bg-emerald-50/60 dark:bg-emerald-950/20'
                    : 'border-slate-200 dark:border-slate-800 bg-slate-50/40 dark:bg-slate-900/40'
                }`}
              >
                {/* Completion badge */}
                {isDone && (
                  <div className="absolute top-2.5 right-2.5 w-5 h-5 rounded-full bg-emerald-500 text-white flex items-center justify-center">
                    <Check className="w-3 h-3 stroke-[3]" />
                  </div>
                )}

                {/* Icon */}
                <div className={`relative ${
                  isActive ? 'drop-shadow-md' : isPending ? 'opacity-40' : ''
                }`}>
                  {step.icon}
                  {isActive && (
                    <div className="absolute -bottom-1.5 left-1/2 -translate-x-1/2 w-4 h-1 bg-sky-400 rounded-full animate-pulse" />
                  )}
                </div>

                {/* Label */}
                <p className={`text-[12px] font-bold text-center leading-tight ${
                  isDone ? 'text-emerald-700 dark:text-emerald-400'
                  : isActive ? 'text-sky-700 dark:text-sky-400'
                  : 'text-slate-400 dark:text-slate-600'
                }`}>
                  {step.label}
                </p>
                <p className={`text-[10px] text-center leading-snug whitespace-pre-line ${
                  isActive || isDone ? 'text-slate-500 dark:text-slate-400' : 'text-slate-300 dark:text-slate-700'
                }`}>
                  {step.sub}
                </p>

                {/* Status tag */}
                {isActive && (
                  <div className="flex items-center gap-1 bg-sky-100 dark:bg-sky-950/60 text-sky-600 dark:text-sky-400 text-[10px] font-bold px-2.5 py-0.5 rounded-full border border-sky-200 dark:border-sky-900/40">
                    <Loader2 className="w-2.5 h-2.5 animate-spin" />
                    In Progress
                  </div>
                )}
                {isPending && (
                  <div className="text-[10px] font-semibold text-slate-400 dark:text-slate-600 border border-slate-200 dark:border-slate-700 px-2.5 py-0.5 rounded-full">
                    Pending
                  </div>
                )}
                {isDone && i < 2 && (
                  <div className="text-[10px] font-semibold text-emerald-600 dark:text-emerald-400">
                    Complete
                  </div>
                )}
              </div>

              {/* Arrow connector */}
              {i < IR_STEPS.length - 1 && (
                <div className="hidden sm:flex items-center mt-[-20px] shrink-0">
                  <ArrowRight className={`w-5 h-5 ${
                    i < active || isComplete ? 'text-sky-400' : 'text-slate-200 dark:text-slate-700'
                  }`} />
                </div>
              )}
            </React.Fragment>
          );
        })}
      </div>

      {/* ---- What is IR? + Live Stats row ---- */}
      <div className="flex flex-col sm:flex-row gap-3">
        {/* What is IR? info card */}
        <div className="flex-1 bg-white dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700/60 rounded-xl p-3.5 text-left">
          <p className="text-xs font-bold text-slate-800 dark:text-slate-100 mb-1.5">What is IR?</p>
          <p className="text-[10px] text-slate-500 dark:text-slate-400 leading-relaxed mb-2">
            Intermediate Representation (IR) is a structured blueprint of your application used to identify test scenarios systematically.
          </p>
          {[
            'Component hierarchy',
            'UI elements & attributes',
            'State & data flow',
            'User interactions',
            'API integrations',
            'Routing & navigation',
          ].map((item) => (
            <div key={item} className="flex items-center gap-1.5 mb-0.5">
              <CheckCircle2 className="w-3 h-3 text-emerald-500 shrink-0" />
              <span className="text-[10px] text-slate-600 dark:text-slate-400">{item}</span>
            </div>
          ))}
        </div>

        {/* Live Stats + tip column */}
        <div className="flex-[2] flex flex-col gap-2">
          {/* Live Stats bar */}
          <div className="bg-white dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700/60 rounded-xl p-3 flex flex-col gap-2">
            <div className="flex items-center gap-1.5 mb-0.5">
              <LayoutGrid className="w-3 h-3 text-sky-500" />
              <span className="text-[10px] font-bold text-slate-600 dark:text-slate-300 uppercase tracking-wider">Live Stats</span>
              {!irStats && <Loader2 className="w-3 h-3 text-sky-400 animate-spin ml-auto" />}
            </div>
            <div className="grid grid-cols-3 sm:grid-cols-6 gap-2">
              {[
                { label: 'Components', value: irStats?.components, icon: Cpu },
                { label: 'UI Elements', value: irStats?.uiElements, icon: LayoutGrid },
                { label: 'States',      value: irStats?.states,     icon: Sliders },
                { label: 'Hooks',       value: irStats?.hooks,      icon: Anchor },
                { label: 'API Calls',   value: irStats?.apiCalls,   icon: Webhook },
                { label: 'Routes',      value: irStats?.routes,     icon: Route },
              ].map(({ label, value, icon: Icon }) => (
                <div key={label} className="flex flex-col items-center gap-0.5 p-2 bg-slate-50/80 dark:bg-slate-900/50 rounded-lg border border-slate-100 dark:border-slate-800">
                  <Icon className="w-3 h-3 text-sky-400 mb-0.5" />
                  <span className="text-[10px] text-slate-400 dark:text-slate-500 leading-none text-center">{label}</span>
                  <span className={`text-sm font-extrabold leading-none ${
                    value != null ? 'text-slate-900 dark:text-white' : 'text-slate-300 dark:text-slate-600'
                  }`}>
                    {value != null ? value : '—'}
                  </span>
                </div>
              ))}
            </div>
          </div>

          {/* Tip card */}
          <div className="bg-sky-50/80 dark:bg-sky-950/20 border border-sky-100 dark:border-sky-900/30 rounded-xl p-3 flex items-start gap-2">
            <Lightbulb className="w-4 h-4 text-sky-500 shrink-0 mt-0.5" />
            <p className="text-[10px] text-sky-700 dark:text-sky-300 leading-relaxed">
              IR will be used to create smarter test cases and comprehensive reports.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}

export default function UploadProjectCard({
  uploadedFile,
  onFileUpload,
  onStartPipeline,
  isExecuting,
  currentStageIndex = -1,
  detectedFramework = "React",
  frameworkVersion = "18.2.0",
  analyzerSubStep = -1,
  irSubStep = -1,
  irStats = null,
}) {
  const fileInputRef = useRef(null);
  const [isDragging, setIsDragging] = useState(false);

  const isStage2Active = currentStageIndex === 1; // Stage 2 Framework Detection active
  const isStage3Active = currentStageIndex === 2 || analyzerSubStep >= 0; // Stage 3 Analyzer active
  const isStage4Active = currentStageIndex === 3 || irSubStep >= 0;       // Stage 4 IR Generator active

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files.length > 0) {
      onFileUpload(e.target.files[0]);
    }
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = () => {
    setIsDragging(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      onFileUpload(e.dataTransfer.files[0]);
    }
  };

  return (
    <div className="bg-white dark:bg-[#1B1E3A] rounded-2xl border border-[#E0E5F2] dark:border-slate-800 p-3 sm:p-4 shadow-sm flex-1 min-h-0 flex flex-col justify-between overflow-hidden transition-colors duration-200">
      {/* Outer Dashed Card Container */}
      <div
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        className={`border-2 border-dashed rounded-xl p-3 sm:p-4 flex-1 min-h-0 flex flex-col items-center justify-center text-center transition-all duration-200 relative overflow-hidden ${
          isDragging
            ? 'border-[#4318FF] bg-[#EAEFFF] dark:bg-[#4318FF]/20 scale-[1.001]'
            : uploadedFile
            ? 'border-[#4318FF]/40 dark:border-[#4318FF]/60 bg-[#F4F7FE] dark:bg-[#11142D]/40'
            : 'border-[#E0E5F2] dark:border-slate-800 bg-[#F4F7FE]/60 dark:bg-[#11142D]/40'
        }`}
      >
        <input
          type="file"
          ref={fileInputRef}
          onChange={handleFileChange}
          accept=".zip,.tar,.gz,.json"
          className="hidden"
        />

        {/* --------------------------------------------------------------------- */}
        {/* DYNAMIC ILLUSTRATION: STAGE 4 IR, STAGE 3 ANALYZER, STAGE 2, UPLOAD   */}
        {/* --------------------------------------------------------------------- */}
        {isStage4Active ? (
          /* -------------------- STAGE 4 IR GENERATOR VIEW -------------------- */
          <IRGeneratorView irSubStep={irSubStep} irStats={irStats} />
        ) : isStage3Active ? (
          /* -------------------- STAGE 3 ANALYZER SUB-STEP STRIP -------------------- */
          <div className="w-full max-w-3xl flex flex-col items-center py-2">
            <AnalyzerSubStepsBar activeSubStep={analyzerSubStep >= 0 ? analyzerSubStep : 0} />
          </div>
        ) : isStage2Active ? (
          /* -------------------- STAGE 2 FRAMEWORK DETECTION GRAPHIC -------------------- */
          <div className="w-full max-w-3xl flex items-center justify-between my-1 relative px-2 select-none">
            {/* LEFT: 3D Folder with Green Checkmark Circle Badge (Completed Step 1) */}
            <div className="relative z-10 flex flex-col items-center shrink-0">
              <div className="w-18 h-14 sm:w-20 sm:h-16 bg-gradient-to-br from-sky-400 to-sky-600 rounded-xl shadow-md shadow-sky-500/25 relative flex items-center justify-center transform hover:scale-105 transition-transform duration-200">
                <div className="absolute -top-1.5 left-2.5 w-6 h-2.5 bg-sky-400 rounded-t-md"></div>
                <div className="w-11 h-9 sm:w-13 sm:h-10 bg-white/30 backdrop-blur-xs rounded-md border border-white/40"></div>
                <div className="w-7 h-7 sm:w-8 sm:h-8 rounded-full bg-emerald-500 text-white shadow-md flex items-center justify-center absolute -bottom-1 -right-1 border-2 border-white dark:border-slate-800">
                  <Check className="w-4 h-4 stroke-[3]" />
                </div>
              </div>
            </div>

            {/* DOTTED BEZIER CURVES & FLOATING CARDS */}
            <div className="flex-1 relative h-20 mx-2 hidden md:block">
              <svg className="absolute inset-0 w-full h-full pointer-events-none" fill="none">
                <path d="M 10 50 Q 50 10 100 30 T 180 40" stroke="#7DD3FC" strokeWidth="1.5" strokeDasharray="3 3" />
              </svg>
              <div className="absolute top-1 left-4 bg-white dark:bg-slate-800 border border-sky-100 dark:border-slate-700 rounded-lg p-1.5 shadow-xs flex items-center gap-1 transform -rotate-6">
                <div className="w-5 h-5 rounded-md bg-sky-50 text-sky-500 flex items-center justify-center">
                  <FileText className="w-3 h-3" />
                </div>
              </div>
              <div className="absolute bottom-1 left-16 bg-white dark:bg-slate-800 border border-sky-100 dark:border-slate-700 rounded-lg p-1.5 shadow-xs flex items-center gap-1 transform rotate-3">
                <div className="w-5 h-5 rounded-md bg-sky-100 text-sky-600 flex items-center justify-center font-bold">
                  <Code2 className="w-3 h-3" />
                </div>
              </div>
              <div className="absolute top-4 right-6 bg-white dark:bg-slate-800 border border-sky-100 dark:border-slate-700 rounded-lg p-1.5 shadow-xs flex items-center gap-1 transform rotate-6">
                <div className="w-5 h-5 rounded-md bg-sky-50 text-sky-500 flex items-center justify-center">
                  <ImageIcon className="w-3 h-3" />
                </div>
              </div>
            </div>

            {/* CENTER: Glowing Circular Badge with Magnifying Glass Icon */}
            <div className="relative z-10 flex flex-col items-center mx-2 shrink-0">
              <div className="relative group">
                <div className="absolute -inset-1.5 bg-gradient-to-r from-sky-300 to-sky-400 rounded-full blur-xs opacity-50 group-hover:opacity-80 transition duration-300"></div>
                <div className="relative w-20 h-20 sm:w-24 sm:h-24 bg-white dark:bg-slate-800 rounded-full shadow-[0_6px_20px_rgba(14,165,233,0.2)] border border-sky-100 dark:border-slate-700 flex items-center justify-center">
                  <div className="w-12 h-12 sm:w-14 sm:h-14 rounded-full bg-sky-50 dark:bg-slate-700/80 text-sky-500 dark:text-sky-400 flex items-center justify-center shadow-inner">
                    <Search className="w-6 h-6 sm:w-7 sm:h-7 stroke-[2.5]" />
                  </div>
                </div>
              </div>
            </div>

            {/* DOTTED BEZIER CURVES */}
            <div className="flex-1 relative h-20 mx-2 hidden md:block">
              <svg className="absolute inset-0 w-full h-full pointer-events-none" fill="none">
                <path d="M 0 40 Q 60 20 140 45" stroke="#7DD3FC" strokeWidth="1.5" strokeDasharray="3 3" />
              </svg>
            </div>

            {/* RIGHT: Framework Detected Result Card */}
            <div className="relative z-10 hidden sm:flex flex-col items-center shrink-0">
              <div className="bg-white dark:bg-slate-800 rounded-2xl border border-sky-100 dark:border-slate-700 shadow-lg p-3.5 sm:p-4 flex items-center gap-3.5 transform hover:scale-102 transition-transform">
                <div className="w-11 h-11 sm:w-12 sm:h-12 rounded-xl bg-sky-50 dark:bg-sky-950/60 flex items-center justify-center shrink-0 border border-sky-100 dark:border-sky-900/40 shadow-xs">
                  <ReactAtomIcon className="w-7 h-7 sm:w-8 sm:h-8 text-sky-400 animate-spin-slow" />
                </div>
                <div className="text-left">
                  <h4 className="font-bold text-slate-800 dark:text-slate-100 text-xs sm:text-sm leading-tight">
                    Framework Detected!
                  </h4>
                  <p className="font-extrabold text-sky-500 dark:text-sky-400 text-sm sm:text-base leading-tight mt-0.5">
                    {detectedFramework || 'React'}
                  </p>
                  <div className="flex items-center gap-2 mt-1">
                    <span className="text-[10px] font-semibold text-slate-400 dark:text-slate-400">
                      Version: {frameworkVersion}
                    </span>
                    <span className="bg-emerald-100 dark:bg-emerald-950/60 text-emerald-600 dark:text-emerald-400 px-2 py-0.5 rounded-full text-[9px] font-bold border border-emerald-200/60 dark:border-emerald-900/40">
                      Supported
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        ) : (
          /* -------------------- INITIAL SCRATCH UPLOAD GRAPHIC -------------------- */
          <div className="w-full max-w-3xl flex items-center justify-between my-1 relative px-2 select-none">
            {/* LEFT: 3D Folder with (+) Circle Badge */}
            <div className="relative z-10 flex flex-col items-center shrink-0">
              <div className="w-18 h-14 sm:w-20 sm:h-16 bg-gradient-to-br from-sky-400 to-sky-600 rounded-xl shadow-md shadow-sky-500/25 relative flex items-center justify-center transform hover:scale-105 transition-transform duration-200">
                <div className="absolute -top-1.5 left-2.5 w-6 h-2.5 bg-sky-400 rounded-t-md"></div>
                <div className="w-11 h-9 sm:w-13 sm:h-10 bg-white/30 backdrop-blur-xs rounded-md border border-white/40"></div>
                <div className="w-7 h-7 sm:w-8 sm:h-8 rounded-full bg-white dark:bg-slate-800 text-sky-500 shadow-md flex items-center justify-center absolute -bottom-1 -right-1 border border-sky-100">
                  <Plus className="w-4 h-4 stroke-[3]" />
                </div>
              </div>
            </div>

            {/* DOTTED BEZIER CURVES & FLOATING CARDS */}
            <div className="flex-1 relative h-20 mx-2 hidden md:block">
              <svg className="absolute inset-0 w-full h-full pointer-events-none" fill="none">
                <path d="M 10 50 Q 50 10 100 30 T 180 40" stroke="#7DD3FC" strokeWidth="1.5" strokeDasharray="3 3" />
              </svg>
              <div className="absolute top-1 left-4 bg-white dark:bg-slate-800 border border-sky-100 dark:border-slate-700 rounded-lg p-1.5 shadow-xs flex items-center gap-1 transform -rotate-6">
                <div className="w-5 h-5 rounded-md bg-sky-50 text-sky-500 flex items-center justify-center">
                  <FileText className="w-3 h-3" />
                </div>
              </div>
              <div className="absolute bottom-1 left-16 bg-white dark:bg-slate-800 border border-sky-100 dark:border-slate-700 rounded-lg p-1.5 shadow-xs flex items-center gap-1 transform rotate-3">
                <div className="w-5 h-5 rounded-md bg-sky-100 text-sky-600 flex items-center justify-center font-bold">
                  <Code2 className="w-3 h-3" />
                </div>
              </div>
              <div className="absolute top-4 right-6 bg-white dark:bg-slate-800 border border-sky-100 dark:border-slate-700 rounded-lg p-1.5 shadow-xs flex items-center gap-1 transform rotate-6">
                <div className="w-5 h-5 rounded-md bg-sky-50 text-sky-500 flex items-center justify-center">
                  <ImageIcon className="w-3 h-3" />
                </div>
              </div>
            </div>

            {/* CENTER: Glowing White Cloud with Upward Arrow */}
            <div className="relative z-10 flex flex-col items-center mx-2 shrink-0">
              <Sparkles className="w-3.5 h-3.5 text-sky-400 absolute -top-2 -left-2 animate-pulse" />
              <Sparkles className="w-4 h-4 text-sky-400 absolute -top-3 -right-3 animate-pulse" />
              <div className="relative group">
                <div className="absolute -inset-1.5 bg-gradient-to-r from-sky-300 to-sky-400 rounded-full blur-xs opacity-40 group-hover:opacity-70 transition duration-300"></div>
                <div className="relative w-24 h-16 sm:w-28 sm:h-18 bg-white dark:bg-slate-800 rounded-[28px] shadow-[0_6px_20px_rgba(14,165,233,0.18)] border border-sky-100 dark:border-slate-700 flex items-center justify-center p-2">
                  <div className="w-9 h-9 sm:w-10 sm:h-10 rounded-full bg-sky-50 dark:bg-slate-700/80 text-sky-500 dark:text-sky-400 flex items-center justify-center shadow-inner">
                    <ArrowUp className="w-5 h-5 sm:w-6 sm:h-6 stroke-[3] transform group-hover:-translate-y-0.5 transition-transform" />
                  </div>
                </div>
              </div>
            </div>

            {/* DOTTED BEZIER CURVES */}
            <div className="flex-1 relative h-20 mx-2 hidden md:block">
              <svg className="absolute inset-0 w-full h-full pointer-events-none" fill="none">
                <path d="M 0 40 Q 60 20 140 45" stroke="#7DD3FC" strokeWidth="1.5" strokeDasharray="3 3" />
              </svg>
            </div>

            {/* RIGHT: Web Browser Mockup Window with Green Checkmark Badge */}
            <div className="relative z-10 hidden sm:flex flex-col items-center shrink-0">
              <div className="w-40 h-28 sm:w-44 sm:h-30 bg-white dark:bg-slate-800 rounded-lg border border-slate-200 dark:border-slate-700 shadow-md p-2.5 relative overflow-hidden flex flex-col justify-between transform -rotate-1">
                <div className="flex items-center gap-1 pb-1.5 border-b border-slate-100 dark:border-slate-700/60">
                  <div className="w-2 h-2 rounded-full bg-emerald-400"></div>
                  <div className="w-2 h-2 rounded-full bg-sky-400"></div>
                  <div className="w-2 h-2 rounded-full bg-sky-300"></div>
                </div>
                <div className="flex-1 mt-1.5 space-y-1.5">
                  <div className="flex items-center gap-1.5">
                    <Check className="w-3 h-3 text-emerald-500 stroke-[3]" />
                    <div className="h-2 bg-sky-200 dark:bg-sky-900/60 rounded-full w-20"></div>
                  </div>
                  <div className="flex items-center gap-1.5">
                    <div className="w-3 h-3 rounded-full border border-sky-300"></div>
                    <div className="h-2 bg-sky-100 dark:bg-slate-700 rounded-full w-24"></div>
                  </div>
                  <div className="flex items-center gap-1.5">
                    <div className="w-3 h-3 rounded-full border border-sky-300"></div>
                    <div className="h-2 bg-sky-100 dark:bg-slate-700 rounded-full w-20"></div>
                  </div>
                </div>
                <div className="absolute -bottom-1 -right-1 w-7 h-7 sm:w-8 sm:h-8 rounded-full bg-emerald-500 text-white flex items-center justify-center shadow-md border-2 border-white dark:border-slate-800">
                  <Check className="w-4 h-4 stroke-[3]" />
                </div>
              </div>
            </div>
          </div>
        )}

        {/* --------------------------------------------------------------------- */}
        {/* COMPACT TEXT & ACTION CONTROLS                                         */}
        {/* --------------------------------------------------------------------- */}
        <h3 className="font-bold text-[#1B2559] dark:text-slate-100 text-sm sm:text-base mt-1">
          {isStage4Active
            ? 'IR Generator in Progress'
            : isStage3Active
            ? 'Analyzing project code...'
            : isStage2Active
            ? 'Detecting framework...'
            : 'Upload Project'}
        </h3>
        <p className="text-[#707EAE] dark:text-[#A3AED0] text-[11px] mt-0.5 mb-2 font-medium">
          {isStage4Active
            ? 'Converting analyzed data into an Intermediate Representation (IR)'
            : isStage3Active
            ? 'Parsing AST, extracting component metadata and dependency graph'
            : isStage2Active
            ? 'Analyzing your project structure'
            : 'Upload your frontend project to generate UI test cases'}
        </p>

        {/* Animated Loading Dots Loader when Stage 2, 3, or 4 active */}
        {(isStage2Active || isStage3Active || isStage4Active) && (
          <div className="flex items-center justify-center gap-1.5 mb-1.5">
            <div className="w-1.5 h-1.5 rounded-full bg-[#7357FF] animate-bounce"></div>
            <div className="w-1.5 h-1.5 rounded-full bg-[#4318FF] animate-bounce [animation-delay:0.2s]"></div>
            <div className="w-1.5 h-1.5 rounded-full bg-[#FF5523] animate-bounce [animation-delay:0.4s]"></div>
          </div>
        )}

        {/* Selected File / Choose Folder Controls */}
        {uploadedFile ? (
          <div className="flex items-center gap-3 bg-white dark:bg-slate-800 border border-[#E0E5F2] dark:border-slate-700 px-3.5 py-1.5 rounded-xl shadow-xs mb-1">
            <FileCode2 className="w-4 h-4 text-[#4318FF] dark:text-[#7357FF]" />
            <div className="text-left">
              <p className="text-xs font-bold text-[#1B2559] dark:text-slate-100 truncate max-w-[220px]">
                {uploadedFile.name}
              </p>
              <p className="text-[10px] text-[#A3AED0]">
                {(uploadedFile.size / 1024).toFixed(1)} KB • Project Files Ready
              </p>
            </div>
            <button
              onClick={() => fileInputRef.current?.click()}
              className="text-xs text-[#4318FF] font-semibold hover:underline ml-2"
            >
              Change
            </button>
          </div>
        ) : (
          /* Choose Folder Button */
          <button
            type="button"
            onClick={() => fileInputRef.current?.click()}
            className="bg-[#4318FF] hover:bg-[#3311CC] active:bg-[#280CA0] text-white font-medium px-4 py-1.5 rounded-xl text-xs flex items-center gap-2 shadow-md shadow-[#4318FF]/20 transition-all transform hover:-translate-y-0.5"
          >
            <Folder className="w-3.5 h-3.5 fill-white/20 stroke-[2]" />
            <span>Choose Folder</span>
          </button>
        )}

        <p className="text-[10px] text-[#A3AED0] dark:text-[#707EAE] mt-1">
          or drag and drop your project folder here
        </p>
      </div>

      {/* COMPACT Start Pipeline Progress Action Bar */}
      <div className="mt-2 flex flex-col items-center justify-center border-t border-[#E0E5F2] dark:border-slate-800/60 pt-2 shrink-0">
        <button
          type="button"
          disabled={isExecuting}
          onClick={onStartPipeline}
          className={`font-semibold px-6 py-2 rounded-xl text-xs flex items-center gap-2 transition-all shadow-md ${
            !isExecuting
              ? 'bg-[#FF5523] hover:bg-[#E0481B] text-white shadow-[#FF5523]/25 hover:shadow-[#FF5523]/35 transform hover:-translate-y-0.5 cursor-pointer'
              : 'bg-[#FF5523]/80 text-white cursor-wait shadow-none'
          }`}
        >
          <Play className={`w-3.5 h-3.5 fill-current ${isExecuting ? 'animate-spin' : ''}`} />
          <span>{isExecuting ? 'Pipeline Execution Running...' : 'Start to Test'}</span>
        </button>

        <p className="text-[10px] text-[#A3AED0] dark:text-slate-500 mt-0.5 font-medium">
          {isExecuting
            ? 'Running pipeline execution across stages...'
            : 'Click to begin pipeline execution'}
        </p>
      </div>
    </div>
  );
}
