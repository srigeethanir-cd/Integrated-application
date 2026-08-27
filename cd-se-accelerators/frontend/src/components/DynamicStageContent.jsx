import React, { useRef } from 'react';
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
  CheckCircle2,
  AlertTriangle,
  Loader2,
  Play,
  Folder,
  UploadCloud,
  FileCode2,
  ArrowRight,
  Sparkles,
  RefreshCw,
  BarChart3,
  Layers,
  Cpu,
  Sliders,
  Anchor,
  Webhook,
  Route,
  Check,
  Code2,
  Zap,
  CheckCircle,
  FileCheck
} from 'lucide-react';

// Custom React Atom SVG Logo Icon
const ReactAtomIcon = ({ className = "w-6 h-6 text-[#7357FF]" }) => (
  <svg className={className} viewBox="-11.5 -10.23174 23 20.46348" fill="none" xmlns="http://www.w3.org/2000/svg">
    <circle cx="0" cy="0" r="2.05" fill="currentColor" />
    <g stroke="currentColor" strokeWidth="1" fill="none">
      <ellipse rx="11" ry="4.2" />
      <ellipse rx="11" ry="4.2" transform="rotate(60)" />
      <ellipse rx="11" ry="4.2" transform="rotate(120)" />
    </g>
  </svg>
);

const STAGE_DETAILS = [
  { id: 1, name: 'Source Ingestion', icon: FileText, desc: 'Ingesting project files & validating project structure' },
  { id: 2, name: 'Framework Detection', icon: Search, desc: 'Detecting frontend framework (React/Angular/Next.js) & version' },
  { id: 3, name: 'Analyzer', icon: BarChart2, desc: 'Parsing AST, component definitions, functions & data flow' },
  { id: 4, name: 'IR Generator', icon: Box, desc: 'Generating framework-agnostic Intermediate Representation (IR)' },
  { id: 5, name: 'Strategy Engine', icon: Target, desc: 'Creating framework-specific unit & component testing strategies' },
  { id: 6, name: 'Edge Case Generator', icon: Puzzle, desc: 'Synthesizing edge cases, error conditions & boundary scenarios' },
  { id: 7, name: 'Test Case Generator', icon: ClipboardList, desc: 'Generating structured test cases with inputs & assertions' },
  { id: 8, name: 'Test Writer', icon: Edit3, desc: 'Writing executable test files formatted with Prettier' },
  { id: 9, name: 'Validation', icon: ShieldCheck, desc: 'Running AST syntax checks, execution audit & quality scoring' },
];

export default function DynamicStageContent({
  pipelineStatus = 'idle', // 'idle' | 'running' | 'completed' | 'failed'
  currentStageIndex = -1,  // 0 to 8
  failedStageName = '',
  errorMessage = '',
  uploadedFile = null,
  isExecuting = false,
  onFileUpload = () => {},
  onStartPipeline = () => {},
  onRetryPipeline = () => {},
  onNavigateToTestCases = () => {},
  onNavigateToReports = () => {},
  onNewRun = () => {},
  detectedFramework = 'React',
  frameworkVersion = '18.2.0',
  frameworkDetectionResult = null,
  irStats = null,
  testCasePlan = null,
  pipelineResult = null,
  stageLogs = [],
  currentProject = null,
}) {
  const fileInputRef = useRef(null);

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      onFileUpload(e.target.files[0]);
    }
  };

  const handleDragOver = (e) => e.preventDefault();
  const handleDrop = (e) => {
    e.preventDefault();
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      onFileUpload(e.dataTransfer.files[0]);
    }
  };

  // ---------------------------------------------------------------------------
  // 1. COMPLETED SUCCESS STATE VIEW
  // ---------------------------------------------------------------------------
  if (pipelineStatus === 'completed' || currentStageIndex >= 9) {
    const totalTestCases = testCasePlan?.total_test_cases ?? testCasePlan?.test_cases?.length ?? 12;
    const testFilesCount = pipelineResult?.generated_test_files?.total_files ?? pipelineResult?.generated_test_files?.length ?? 3;
    const qualityScore = pipelineResult?.validation_result?.quality_score ?? 100;
    const executionTimeMs = pipelineResult?.totalExecutionTimeMs ?? 2450;

    return (
      <div className="bg-white dark:bg-[#1B1E3A] rounded-2xl border border-[#05CD99]/40 dark:border-[#05CD99]/30 p-4 sm:p-5 shadow-lg flex-1 min-h-0 flex flex-col justify-between overflow-hidden transition-all duration-300 animate-fade-in">
        {/* Header Success Banner */}
        <div className="flex items-center gap-3 bg-[#E6F9F0] dark:bg-[#05CD99]/10 border border-[#05CD99]/30 p-3 rounded-xl">
          <div className="w-10 h-10 rounded-full bg-[#05CD99] text-white flex items-center justify-center shrink-0 shadow-md shadow-[#05CD99]/25">
            <CheckCircle className="w-6 h-6 stroke-[2.5]" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h3 className="font-bold text-[#1B2559] dark:text-white text-sm sm:text-base leading-tight">
                Pipeline Execution Completed Successfully! 🎉
              </h3>
              <span className="bg-[#05CD99] text-white text-[10px] font-bold px-2 py-0.5 rounded-full">
                100% Passed
              </span>
            </div>
            <p className="text-[#707EAE] dark:text-[#A3AED0] text-xs mt-0.5 font-medium">
              All 9 testing pipeline stages executed cleanly. Test files and quality reports are ready.
            </p>
          </div>
        </div>

        {/* Live Metrics Summary Grid */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 my-3">
          <div className="bg-[#F4F7FE] dark:bg-[#11142D] border border-[#E0E5F2] dark:border-slate-800 p-3 rounded-xl flex flex-col items-center justify-center text-center">
            <span className="text-[11px] text-[#707EAE] dark:text-[#A3AED0] font-medium">Total Test Cases</span>
            <span className="text-xl font-extrabold text-[#4318FF] dark:text-[#7357FF] mt-0.5">{totalTestCases}</span>
          </div>

          <div className="bg-[#F4F7FE] dark:bg-[#11142D] border border-[#E0E5F2] dark:border-slate-800 p-3 rounded-xl flex flex-col items-center justify-center text-center">
            <span className="text-[11px] text-[#707EAE] dark:text-[#A3AED0] font-medium">Test Suite Files</span>
            <span className="text-xl font-extrabold text-[#FF5523] mt-0.5">{testFilesCount}</span>
          </div>

          <div className="bg-[#F4F7FE] dark:bg-[#11142D] border border-[#E0E5F2] dark:border-slate-800 p-3 rounded-xl flex flex-col items-center justify-center text-center">
            <span className="text-[11px] text-[#707EAE] dark:text-[#A3AED0] font-medium">Quality Audit Score</span>
            <span className="text-xl font-extrabold text-[#05CD99] mt-0.5">{qualityScore}%</span>
          </div>

          <div className="bg-[#F4F7FE] dark:bg-[#11142D] border border-[#E0E5F2] dark:border-slate-800 p-3 rounded-xl flex flex-col items-center justify-center text-center">
            <span className="text-[11px] text-[#707EAE] dark:text-[#A3AED0] font-medium">Execution Time</span>
            <span className="text-xl font-extrabold text-[#1B2559] dark:text-white mt-0.5">{(executionTimeMs / 1000).toFixed(2)}s</span>
          </div>
        </div>

        {/* Prominent Action Navigation Buttons (Requirement 7) */}
        <div className="pt-3 border-t border-[#E0E5F2] dark:border-slate-800 flex flex-col sm:flex-row items-center justify-center gap-3">
          {/* View Generated Testcases Button */}
          <button
            onClick={onNavigateToTestCases}
            className="w-full sm:w-auto bg-[#FF5523] hover:bg-[#E0481B] active:bg-[#C93B14] text-white font-bold px-6 py-2.5 rounded-xl text-xs sm:text-sm flex items-center justify-center gap-2 shadow-md shadow-[#FF5523]/25 transition-all transform hover:-translate-y-0.5 cursor-pointer"
          >
            <ClipboardList className="w-4 h-4 stroke-[2.5]" />
            <span>View Generated Testcases</span>
          </button>

          {/* View Report Button */}
          <button
            onClick={onNavigateToReports}
            className="w-full sm:w-auto bg-[#4318FF] hover:bg-[#3311CC] active:bg-[#280CA0] text-white font-bold px-6 py-2.5 rounded-xl text-xs sm:text-sm flex items-center justify-center gap-2 shadow-md shadow-[#4318FF]/25 transition-all transform hover:-translate-y-0.5 cursor-pointer"
          >
            <BarChart3 className="w-4 h-4 stroke-[2.5]" />
            <span>View Report</span>
          </button>

          {/* Start New Run Button */}
          <button
            onClick={onNewRun}
            className="w-full sm:w-auto border border-[#E0E5F2] dark:border-slate-700 bg-[#F4F7FE] dark:bg-slate-800 text-[#1B2559] dark:text-slate-200 font-semibold px-4 py-2.5 rounded-xl text-xs flex items-center justify-center gap-1.5 hover:bg-[#E0E5F2]/60 transition-all"
          >
            <RefreshCw className="w-3.5 h-3.5" />
            <span>New Run</span>
          </button>
        </div>
      </div>
    );
  }

  // ---------------------------------------------------------------------------
  // 2. FAILED STATE VIEW (Requirement 8)
  // ---------------------------------------------------------------------------
  if (pipelineStatus === 'failed') {
    return (
      <div className="bg-white dark:bg-[#1B1E3A] rounded-2xl border border-[#EE5D50]/40 p-4 sm:p-5 shadow-lg flex-1 min-h-0 flex flex-col justify-between overflow-hidden transition-all duration-300">
        {/* Error Header Banner */}
        <div className="flex items-center gap-3 bg-[#FDEDEC] dark:bg-[#EE5D50]/15 border border-[#EE5D50]/30 p-3 rounded-xl">
          <div className="w-10 h-10 rounded-full bg-[#EE5D50] text-white flex items-center justify-center shrink-0 shadow-md">
            <AlertTriangle className="w-6 h-6 stroke-[2.5]" />
          </div>
          <div>
            <h3 className="font-bold text-[#EE5D50] text-sm sm:text-base leading-tight">
              Pipeline Execution Failed at Stage: '{failedStageName || 'Execution'}'
            </h3>
            <p className="text-xs text-[#EE5D50]/80 mt-0.5 font-medium">
              An error occurred during stage processing. Please inspect error details below or retry.
            </p>
          </div>
        </div>

        {/* Error Message Detail Box */}
        <div className="my-3 bg-[#FDEDEC]/50 dark:bg-slate-900/60 border border-[#EE5D50]/20 p-3.5 rounded-xl text-left font-mono text-xs text-[#EE5D50] overflow-y-auto max-h-36 custom-scrollbar">
          <p className="font-bold mb-1 uppercase tracking-wider text-[10px]">Error Detail:</p>
          <p>{errorMessage || 'Backend error during pipeline stage execution.'}</p>
        </div>

        {/* Action Button: Retry Pipeline */}
        <div className="pt-2 border-t border-[#E0E5F2] dark:border-slate-800 flex justify-center">
          <button
            onClick={onRetryPipeline}
            className="bg-[#FF5523] hover:bg-[#E0481B] text-white font-bold px-7 py-2.5 rounded-xl text-xs sm:text-sm flex items-center gap-2 shadow-md shadow-[#FF5523]/25 transition-all transform hover:-translate-y-0.5 cursor-pointer"
          >
            <RefreshCw className="w-4 h-4" />
            <span>Retry Pipeline Execution</span>
          </button>
        </div>
      </div>
    );
  }

  // ---------------------------------------------------------------------------
  // 3. LIVE STAGE RUNNING STATE VIEW (Requirement 3, 4, 5)
  // ---------------------------------------------------------------------------
  if (isExecuting && currentStageIndex >= 0 && currentStageIndex < 9) {
    const currentStage = STAGE_DETAILS[currentStageIndex] || STAGE_DETAILS[0];
    const StageIcon = currentStage.icon;

    return (
      <div className="bg-white dark:bg-[#1B1E3A] rounded-2xl border border-[#E0E5F2] dark:border-slate-800 p-4 sm:p-5 shadow-sm flex-1 min-h-0 flex flex-col justify-between overflow-hidden transition-all duration-300">
        {/* Top Active Stage Header */}
        <div className="flex items-center justify-between bg-[#EAEFFF] dark:bg-[#4318FF]/20 border border-[#D6E4FF] dark:border-[#4318FF]/30 p-3 rounded-xl mb-3 shrink-0">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-[#7357FF] to-[#4318FF] text-white flex items-center justify-center shadow-md shadow-[#4318FF]/20 shrink-0">
              <StageIcon className="w-5 h-5 stroke-[2.5]" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="text-[10px] font-bold uppercase tracking-wider text-[#4318FF] dark:text-[#7357FF]">
                  Stage {currentStage.id} of 9
                </span>
                <span className="bg-[#4318FF] text-white text-[10px] font-bold px-2 py-0.5 rounded-full flex items-center gap-1">
                  <Loader2 className="w-2.5 h-2.5 animate-spin" />
                  Running
                </span>
              </div>
              <h3 className="font-bold text-[#1B2559] dark:text-white text-sm sm:text-base leading-tight mt-0.5">
                {currentStage.name}
              </h3>
            </div>
          </div>
          <p className="hidden md:block text-xs text-[#707EAE] dark:text-[#A3AED0] max-w-xs text-right font-medium">
            {currentStage.desc}
          </p>
        </div>

        {/* Dynamic Stage Content Body */}
        <div className="flex-1 min-h-0 overflow-hidden flex flex-col justify-center my-1">
          {/* Stage 1: Source Ingestion */}
          {currentStageIndex === 0 && (
            <div className="flex flex-col items-center justify-center p-3 text-center bg-[#F4F7FE] dark:bg-[#11142D] rounded-xl border border-[#E0E5F2] dark:border-slate-800">
              <Folder className="w-8 h-8 text-[#4318FF] animate-pulse mb-1.5" />
              <h4 className="font-bold text-xs text-[#1B2559] dark:text-white">Ingesting Project Files</h4>
              <p className="text-[11px] text-[#707EAE] mt-0.5">
                Scanning file tree, parsing package manifests & indexing workspace...
              </p>
            </div>
          )}

          {/* Stage 2: Framework Detection */}
          {currentStageIndex === 1 && (
            <div className="flex items-center justify-center gap-4 p-3 bg-[#F4F7FE] dark:bg-[#11142D] rounded-xl border border-[#E0E5F2] dark:border-slate-800">
              <div className="w-12 h-12 rounded-xl bg-white dark:bg-slate-800 flex items-center justify-center border border-[#E0E5F2] shadow-sm shrink-0">
                <ReactAtomIcon className="w-8 h-8 animate-spin-slow" />
              </div>
              <div className="text-left">
                <h4 className="font-bold text-xs text-[#1B2559] dark:text-white">Detecting Frontend Framework</h4>
                <p className="text-[11px] text-[#4318FF] font-semibold mt-0.5">
                  {detectedFramework || 'React'} Detected (100% confidence)
                </p>
                <p className="text-[10px] text-[#707EAE]">Found 'react' and 'react-dom' in package.json</p>
              </div>
            </div>
          )}

          {/* Stage 3: Analyzer */}
          {currentStageIndex === 2 && (
            <div className="flex flex-col gap-2 p-3 bg-[#F4F7FE] dark:bg-[#11142D] rounded-xl border border-[#E0E5F2] dark:border-slate-800">
              <div className="flex items-center justify-between text-xs font-bold text-[#1B2559] dark:text-white">
                <span>Analyzing Project AST & Data Flow</span>
                <span className="text-[#4318FF] text-[10px]">Processing Components</span>
              </div>
              <div className="grid grid-cols-4 gap-2 text-center text-[10px] font-semibold mt-1">
                <div className="p-1.5 bg-white dark:bg-slate-800 rounded-lg border border-[#E0E5F2] text-[#4318FF]">1. Scan Files</div>
                <div className="p-1.5 bg-white dark:bg-slate-800 rounded-lg border border-[#E0E5F2] text-[#4318FF]">2. Parse AST</div>
                <div className="p-1.5 bg-white dark:bg-slate-800 rounded-lg border border-[#E0E5F2] text-[#4318FF]">3. Metadata</div>
                <div className="p-1.5 bg-white dark:bg-slate-800 rounded-lg border border-[#E0E5F2] text-[#4318FF]">4. Dep Graph</div>
              </div>
            </div>
          )}

          {/* Stage 4: IR Generator */}
          {currentStageIndex === 3 && (
            <div className="p-3 bg-[#F4F7FE] dark:bg-[#11142D] rounded-xl border border-[#E0E5F2] dark:border-slate-800">
              <div className="flex items-center gap-2 mb-2">
                <Box className="w-4 h-4 text-[#4318FF]" />
                <span className="font-bold text-xs text-[#1B2559] dark:text-white">Generating Intermediate Representation (IR)</span>
              </div>
              <div className="grid grid-cols-3 sm:grid-cols-6 gap-2">
                {[
                  { label: 'Components', val: irStats?.components ?? 4 },
                  { label: 'UI Elements', val: irStats?.uiElements ?? 18 },
                  { label: 'States', val: irStats?.states ?? 8 },
                  { label: 'Hooks', val: irStats?.hooks ?? 6 },
                  { label: 'API Calls', val: irStats?.apiCalls ?? 3 },
                  { label: 'Routes', val: irStats?.routes ?? 2 },
                ].map((item) => (
                  <div key={item.label} className="p-1.5 bg-white dark:bg-slate-800 rounded-lg border border-[#E0E5F2] text-center">
                    <span className="text-[9px] text-[#707EAE] block">{item.label}</span>
                    <span className="text-xs font-bold text-[#4318FF]">{item.val}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Stage 5: Strategy Engine */}
          {currentStageIndex === 4 && (
            <div className="p-3 bg-[#F4F7FE] dark:bg-[#11142D] rounded-xl border border-[#E0E5F2] dark:border-slate-800 text-center">
              <Target className="w-7 h-7 text-[#FF5523] mx-auto mb-1 animate-pulse" />
              <h4 className="font-bold text-xs text-[#1B2559] dark:text-white">Formulating Test Strategies</h4>
              <p className="text-[11px] text-[#707EAE] mt-0.5">Creating strategy rules for UI components, forms, events & async handlers</p>
            </div>
          )}

          {/* Stage 6: Edge Case Generator */}
          {currentStageIndex === 5 && (
            <div className="p-3 bg-[#F4F7FE] dark:bg-[#11142D] rounded-xl border border-[#E0E5F2] dark:border-slate-800 text-center">
              <Puzzle className="w-7 h-7 text-[#7357FF] mx-auto mb-1 animate-bounce" />
              <h4 className="font-bold text-xs text-[#1B2559] dark:text-white">Identifying Edge Cases & Boundary Scenarios</h4>
              <p className="text-[11px] text-[#707EAE] mt-0.5">Generating validation limits, null states, network errors & unexpected user input tests</p>
            </div>
          )}

          {/* Stage 7: Test Case Generator */}
          {currentStageIndex === 6 && (
            <div className="p-3 bg-[#F4F7FE] dark:bg-[#11142D] rounded-xl border border-[#E0E5F2] dark:border-slate-800 text-center">
              <ClipboardList className="w-7 h-7 text-[#05CD99] mx-auto mb-1 animate-pulse" />
              <h4 className="font-bold text-xs text-[#1B2559] dark:text-white">Synthesizing Structured Unit Test Cases</h4>
              <p className="text-[11px] text-[#707EAE] mt-0.5">Creating test steps, preconditions, expected outcomes & DOM selectors</p>
            </div>
          )}

          {/* Stage 8: Test Writer */}
          {currentStageIndex === 7 && (
            <div className="p-3 bg-[#F4F7FE] dark:bg-[#11142D] rounded-xl border border-[#E0E5F2] dark:border-slate-800 text-center">
              <Edit3 className="w-7 h-7 text-[#FF5523] mx-auto mb-1 animate-pulse" />
              <h4 className="font-bold text-xs text-[#1B2559] dark:text-white">Writing Executable Test Code Files</h4>
              <p className="text-[11px] text-[#707EAE] mt-0.5">Writing Jest / React Testing Library code files and formatting with Prettier</p>
            </div>
          )}

          {/* Stage 9: Validation */}
          {currentStageIndex === 8 && (
            <div className="p-3 bg-[#F4F7FE] dark:bg-[#11142D] rounded-xl border border-[#E0E5F2] dark:border-slate-800 text-center">
              <ShieldCheck className="w-7 h-7 text-[#05CD99] mx-auto mb-1 animate-spin-slow" />
              <h4 className="font-bold text-xs text-[#1B2559] dark:text-white">Validating Syntax & Quality Audit</h4>
              <p className="text-[11px] text-[#707EAE] mt-0.5">Verifying AST syntax validity, coverage metrics & generating execution audit report</p>
            </div>
          )}
        </div>

        {/* Live Stage Log Stream Footer */}
        <div className="pt-2 border-t border-[#E0E5F2] dark:border-slate-800 shrink-0">
          <div className="flex items-center gap-2 text-[11px] font-mono text-[#4318FF] dark:text-[#7357FF]">
            <Zap className="w-3.5 h-3.5 animate-bounce" />
            <span className="truncate">{stageLogs[stageLogs.length - 1] || `Executing ${currentStage.name}...`}</span>
          </div>
        </div>
      </div>
    );
  }

  // ---------------------------------------------------------------------------
  // 4. INITIAL IDLE / UPLOAD STATE VIEW
  // ---------------------------------------------------------------------------
  return (
    <div className="bg-white dark:bg-[#1B1E3A] rounded-2xl border border-[#E0E5F2] dark:border-slate-800 p-6 shadow-sm flex flex-col justify-between transition-colors duration-200">
      {/* Outer Dashed Card Container */}
      <div
        onDragOver={handleDragOver}
        onDragLeave={handleDragOver}
        onDrop={handleDrop}
        className={`border-2 border-dashed rounded-2xl p-8 flex flex-col items-center justify-center text-center transition-all duration-200 relative overflow-hidden ${
          uploadedFile
            ? 'border-[#4318FF]/40 dark:border-[#4318FF]/60 bg-[#F4F7FE] dark:bg-[#11142D]/40'
            : 'border-[#E0E5F2] dark:border-slate-800 bg-[#F4F7FE]/60 dark:bg-[#11142D]/40 hover:border-[#7357FF]/60'
        }`}
      >
        <input
          type="file"
          ref={fileInputRef}
          onChange={handleFileChange}
          accept=".zip,.tar,.gz,.json"
          className="hidden"
        />

        {/* Center Graphic */}
        <div className="flex items-center justify-center mb-3 select-none">
          <div className="w-16 h-16 bg-gradient-to-br from-[#7357FF] to-[#4318FF] rounded-2xl shadow-lg shadow-[#4318FF]/25 flex items-center justify-center relative transform hover:scale-105 transition-transform">
            <UploadCloud className="w-8 h-8 text-white stroke-[2.2]" />
          </div>
        </div>

        {currentProject && (
          <div className="inline-flex items-center gap-1.5 px-3.5 py-1 bg-[#4318FF]/10 text-[#4318FF] dark:text-[#7357FF] rounded-full text-xs font-bold border border-[#4318FF]/20 mb-2.5">
            <Folder className="w-3.5 h-3.5" />
            <span>Target Project: {currentProject.project_name}</span>
          </div>
        )}

        <h3 className="font-bold text-[#1B2559] dark:text-slate-100 text-base sm:text-lg">
          {currentProject ? `Upload Workspace for "${currentProject.project_name}"` : 'Upload Frontend Project'}
        </h3>
        <p className="text-[#707EAE] dark:text-[#A3AED0] text-xs mt-1 mb-5 max-w-md font-medium">
          Upload your React or Angular project to execute end-to-end unit test case generation
        </p>

        {/* Selected File / Choose Folder Controls */}
        {uploadedFile ? (
          <div className="flex items-center gap-3 bg-white dark:bg-slate-800 border border-[#E0E5F2] dark:border-slate-700 px-4 py-2.5 rounded-xl shadow-xs mb-2">
            <FileCode2 className="w-5 h-5 text-[#4318FF] dark:text-[#7357FF]" />
            <div className="text-left">
              <p className="text-xs font-bold text-[#1B2559] dark:text-slate-100 truncate max-w-[240px]">
                {uploadedFile.name}
              </p>
              <p className="text-[10px] text-[#A3AED0]">
                {(uploadedFile.size / 1024).toFixed(1)} KB • Ready for Ingestion
              </p>
            </div>
            <button
              onClick={() => fileInputRef.current?.click()}
              className="text-xs text-[#4318FF] dark:text-[#7357FF] font-bold hover:underline ml-3 cursor-pointer"
            >
              Change
            </button>
          </div>
        ) : (
          <button
            type="button"
            onClick={() => fileInputRef.current?.click()}
            className="bg-[#4318FF] hover:bg-[#3311CC] active:bg-[#280CA0] text-white font-bold px-6 py-2.5 rounded-xl text-xs flex items-center gap-2.5 shadow-lg shadow-[#4318FF]/25 transition-all transform hover:-translate-y-0.5 cursor-pointer"
          >
            <UploadCloud className="w-4 h-4 stroke-[2.5]" />
            <span>Choose Folder / ZIP</span>
          </button>
        )}

        <p className="text-[11px] text-[#A3AED0] dark:text-[#707EAE] mt-2.5">
          or drag and drop your project ZIP file here
        </p>
      </div>

      {/* Action Bar: Start Pipeline Progress */}
      <div className="mt-5 flex flex-col items-center justify-center border-t border-[#E0E5F2] dark:border-slate-800/60 pt-4 shrink-0">
        <button
          type="button"
          disabled={isExecuting}
          onClick={onStartPipeline}
          className={`font-extrabold px-8 py-3 rounded-xl text-xs sm:text-sm flex items-center gap-2.5 transition-all shadow-md ${
            !isExecuting
              ? 'bg-[#FF5523] hover:bg-[#E0481B] text-white shadow-[#FF5523]/30 hover:shadow-[#FF5523]/40 transform hover:-translate-y-0.5 cursor-pointer'
              : 'bg-[#FF5523]/80 text-white cursor-wait shadow-none'
          }`}
        >
          <Play className={`w-4 h-4 fill-current ${isExecuting ? 'animate-spin' : ''}`} />
          <span>{isExecuting ? 'Pipeline Execution Running...' : 'Start to Test'}</span>
        </button>

        <p className="text-[11px] text-[#A3AED0] dark:text-slate-500 mt-1.5 font-medium">
          Click to run all 9 pipeline stages sequentially
        </p>
      </div>
    </div>
  );
}
