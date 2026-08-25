import React, { useState, useEffect } from 'react';
import { 
  Zap, 
  Play, 
  CheckCircle2, 
  AlertTriangle, 
  FileCode, 
  RefreshCw, 
  Layers, 
  ArrowRight, 
  Plus, 
  Code2, 
  Activity, 
  Clock, 
  Percent,
  CheckCircle,
  PlusCircle,
  MinusCircle,
  HelpCircle
} from 'lucide-react';
import { 
  analyzeChangeImpact, 
  runChangeImpactTests, 
  runTestExecution 
} from '../services/apiService';

const IMPACT_LEVEL_STYLES = {
  HIGH: 'bg-red-50 text-red-600 dark:bg-red-950/40 dark:text-red-400 border border-red-200 dark:border-red-900/30',
  MEDIUM: 'bg-amber-50 text-amber-600 dark:bg-amber-950/40 dark:text-amber-400 border border-amber-200 dark:border-amber-900/30',
  LOW: 'bg-sky-50 text-sky-600 dark:bg-sky-950/40 dark:text-sky-400 border border-sky-200 dark:border-sky-900/30',
};

export default function ChangeImpact({ currentProject, pipelineRunId }) {
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [analysisResult, setAnalysisResult] = useState(null);
  const [analysisError, setAnalysisError] = useState('');

  const [isExecuting, setIsExecuting] = useState(false);
  const [executionResult, setExecutionResult] = useState(null);
  const [executionError, setExecutionError] = useState('');

  // Automatically analyze on mount or project changes
  useEffect(() => {
    if (currentProject) {
      handleAnalyze();
    }
  }, [currentProject, pipelineRunId]);

  const handleAnalyze = async () => {
    const runId = pipelineRunId || currentProject?.latest_run?.id || currentProject?.latest_run_id;
    const projectId = currentProject?.id;
    const projectPath = currentProject?.project_path;

    if (!runId) {
      setAnalysisError('No pipeline run ID found to run analysis.');
      return;
    }

    setIsAnalyzing(true);
    setAnalysisError('');
    setAnalysisResult(null);
    setExecutionResult(null);
    setExecutionError('');

    try {
      // Pass null as changedFiles to trigger automatic snapshot comparison
      const data = await analyzeChangeImpact(projectPath, null, runId, projectId);
      setAnalysisResult(data);
    } catch (err) {
      setAnalysisError(err.message || 'Failed to automatically analyze change impact.');
    } finally {
      setIsAnalyzing(false);
    }
  };

  const handleRunImpactedTests = async () => {
    const runId = pipelineRunId || currentProject?.latest_run?.id || currentProject?.latest_run_id;
    
    setIsExecuting(true);
    setExecutionError('');
    setExecutionResult(null);

    try {
      // Running tests with null changedFiles to execute the recommended subset saved on backend
      const result = await runChangeImpactTests(runId, null);
      setExecutionResult(result);
    } catch (err) {
      setExecutionError(err.message || 'Failed to run recommended tests.');
    } finally {
      setIsExecuting(false);
    }
  };

  const handleRunFullSuite = async () => {
    const runId = pipelineRunId || currentProject?.latest_run?.id || currentProject?.latest_run_id;
    
    setIsExecuting(true);
    setExecutionError('');
    setExecutionResult(null);

    try {
      // Fallback/standard run execution service
      const result = await runChangeImpactTests(runId, ["ALL_TESTS_FORCE_DIFF"]);
      setExecutionResult(result);
    } catch (err) {
      setExecutionError(err.message || 'Failed to execute full test suite.');
    } finally {
      setIsExecuting(false);
    }
  };

  // Group tests by impact level
  const groupedRecommendations = analysisResult ? {
    HIGH: analysisResult.recommended_tests.filter(t => t.impact_level === 'HIGH'),
    MEDIUM: analysisResult.recommended_tests.filter(t => t.impact_level === 'MEDIUM'),
    LOW: analysisResult.recommended_tests.filter(t => t.impact_level === 'LOW')
  } : { HIGH: [], MEDIUM: [], LOW: [] };

  return (
    <div className="space-y-6">
      {/* Header Info */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-100 dark:border-slate-800 pb-5">
        <div>
          <h2 className="text-xl font-bold text-slate-900 dark:text-white flex items-center gap-2">
            <Zap className="w-5 h-5 text-amber-500 fill-amber-500/20" />
            Change Impact Smart Test Selection
          </h2>
          <p className="text-slate-500 text-xs mt-1">
            Automatic snapshot-comparison system identifying added, modified, or deleted files to recommend relevant tests.
          </p>
        </div>
        <div className="flex items-center gap-2 shrink-0">
          <button
            onClick={handleAnalyze}
            disabled={isAnalyzing || !currentProject}
            className={`bg-[#4318FF] hover:bg-[#3411D4] active:bg-[#270BA3] text-white px-5 py-2.5 rounded-xl text-xs font-bold flex items-center gap-2 shadow-md shadow-[#4318FF]/20 transition-all ${
              isAnalyzing ? 'opacity-70 cursor-not-allowed' : 'cursor-pointer hover:-translate-y-0.5'
            }`}
          >
            {isAnalyzing ? (
              <>
                <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                Analyzing Snapshot...
              </>
            ) : (
              <>
                <RefreshCw className="w-3.5 h-3.5" />
                Analyze Impact
              </>
            )}
          </button>
        </div>
      </div>

      {/* Analysis Error */}
      {analysisError && (
        <div className="bg-red-50/50 dark:bg-red-950/20 border border-red-200 dark:border-red-900/30 text-red-600 dark:text-red-400 px-4.5 py-3 rounded-2xl text-xs font-semibold flex items-center gap-2">
          <AlertTriangle className="w-4 h-4 shrink-0" />
          {analysisError}
        </div>
      )}

      {/* Loading state */}
      {isAnalyzing && (
        <div className="flex flex-col items-center justify-center py-20 gap-3 border border-dashed border-slate-200 dark:border-slate-800 rounded-2xl bg-slate-50/30 dark:bg-slate-900/10">
          <RefreshCw className="w-8 h-8 text-[#4318FF] animate-spin" />
          <p className="text-xs font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wider">
            Comparing Workspace Snapshots...
          </p>
        </div>
      )}

      {/* Analysis Results Display */}
      {analysisResult && !isAnalyzing && (
        <div className="space-y-6 animate-in fade-in slide-in-from-bottom-2 duration-200">
          
          {/* First Upload / Baseline Notification */}
          {analysisResult.first_upload && (
            <div className="bg-sky-50/50 dark:bg-sky-950/20 border border-sky-200 dark:border-sky-900/30 rounded-2xl p-5 flex items-start gap-3">
              <HelpCircle className="w-5 h-5 text-sky-500 shrink-0 mt-0.5" />
              <div className="space-y-1">
                <h4 className="font-bold text-sky-850 dark:text-sky-350 text-sm">Baseline Snapshot Registered</h4>
                <p className="text-slate-550 dark:text-slate-400 text-xs leading-relaxed">
                  This is the first version of this project. A baseline snapshot has been created. Subsequent uploads will automatically compare files against this baseline version.
                </p>
              </div>
            </div>
          )}

          {/* Change Summary Card */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            
            {/* Diff Summary */}
            <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-5 space-y-4.5 shadow-xs">
              <h3 className="font-bold text-xs uppercase tracking-wider text-slate-400">Change Summary</h3>
              
              <div className="grid grid-cols-2 gap-4">
                <div className="bg-emerald-50/40 dark:bg-emerald-950/10 border border-emerald-100 dark:border-emerald-950/30 p-3 rounded-xl flex items-center justify-between">
                  <span className="text-xs text-slate-500 font-medium flex items-center gap-1.5">
                    <span className="w-2 h-2 rounded-full bg-emerald-500" />
                    Added
                  </span>
                  <span className="font-bold text-emerald-600 dark:text-emerald-400 text-base">
                    {analysisResult.change_summary?.added ?? 0}
                  </span>
                </div>

                <div className="bg-red-50/40 dark:bg-red-950/10 border border-red-100 dark:border-red-950/30 p-3 rounded-xl flex items-center justify-between">
                  <span className="text-xs text-slate-500 font-medium flex items-center gap-1.5">
                    <span className="w-2 h-2 rounded-full bg-red-500" />
                    Modified
                  </span>
                  <span className="font-bold text-red-500 text-base">
                    {analysisResult.change_summary?.modified ?? 0}
                  </span>
                </div>

                <div className="bg-slate-50 dark:bg-slate-800/20 border border-slate-150 dark:border-slate-800 p-3 rounded-xl flex items-center justify-between">
                  <span className="text-xs text-slate-500 font-medium flex items-center gap-1.5">
                    <span className="w-2 h-2 rounded-full bg-[#707EAE]" />
                    Deleted
                  </span>
                  <span className="font-bold text-slate-600 dark:text-slate-400 text-base">
                    {analysisResult.change_summary?.deleted ?? 0}
                  </span>
                </div>

                <div className="bg-slate-50/40 dark:bg-slate-900 border border-slate-100 dark:border-slate-800 p-3 rounded-xl flex items-center justify-between">
                  <span className="text-xs text-slate-500 font-medium flex items-center gap-1.5">
                    <span className="w-2 h-2 rounded-full bg-slate-400" />
                    Unchanged
                  </span>
                  <span className="font-bold text-slate-500 text-base">
                    {analysisResult.change_summary?.unchanged ?? 0}
                  </span>
                </div>
              </div>
            </div>

            {/* Impact Metric & Rating */}
            <div className="lg:col-span-2 bg-gradient-to-r from-amber-50/50 to-white dark:from-amber-950/10 dark:to-[#1B1E3A] border border-amber-250/60 dark:border-[#2B3674]/55 rounded-2xl p-5 flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-6 shadow-sm">
              <div className="space-y-2">
                <div className="flex items-center gap-2">
                  <span className={`text-[10px] font-extrabold px-2.5 py-0.5 rounded-full ${IMPACT_LEVEL_STYLES[analysisResult.impact_level] || IMPACT_LEVEL_STYLES.LOW}`}>
                    {analysisResult.impact_level} IMPACT RATING
                  </span>
                  <span className="text-xs text-slate-400 font-semibold font-mono">Score: {analysisResult.impact_score}/100</span>
                </div>
                <h4 className="font-bold text-slate-800 dark:text-white text-base sm:text-lg leading-snug">
                  Recommended subset: {analysisResult.recommended_tests_count} / {analysisResult.total_tests} test cases.
                </h4>
                <p className="text-[11px] text-slate-400">
                  Calculated automatically by static traversal over workspace files.
                </p>
              </div>

              <div className="flex flex-row sm:flex-col items-center justify-center bg-white dark:bg-slate-900/60 p-4 rounded-xl border border-slate-150 dark:border-slate-800 shrink-0 text-center gap-2 min-w-[120px]">
                <span className="text-[10px] text-slate-400 font-bold uppercase tracking-wider">Execution Reduction</span>
                <span className="text-2xl font-black text-emerald-600 dark:text-emerald-450">{analysisResult.estimated_reduction_percent}%</span>
              </div>
            </div>
          </div>

          {/* Trigger Test Actions Panel */}
          <div className="bg-slate-50/50 dark:bg-slate-800/10 border border-slate-200 dark:border-slate-800 rounded-2xl p-5 flex flex-col md:flex-row md:items-center justify-between gap-4">
            <div className="space-y-0.5">
              <h4 className="font-bold text-slate-800 dark:text-white text-xs uppercase tracking-wider">Execution Pipeline</h4>
              <p className="text-slate-500 text-xs">Run execution pipeline on selected files, or execute full suite.</p>
            </div>

            <div className="flex flex-wrap items-center gap-3 shrink-0">
              <button
                onClick={handleRunImpactedTests}
                disabled={isExecuting || analysisResult.recommended_tests_count === 0}
                className={`bg-amber-500 hover:bg-amber-600 active:bg-amber-700 text-white px-5 py-2.5 rounded-xl text-xs font-bold flex items-center gap-2 shadow-md shadow-amber-500/20 transition-all ${
                  isExecuting ? 'opacity-70 cursor-not-allowed' : 'cursor-pointer hover:-translate-y-0.5'
                }`}
              >
                <Play className="w-4 h-4 fill-white" />
                Run Impacted Tests ({analysisResult.recommended_tests_count})
              </button>
              <button
                onClick={handleRunFullSuite}
                disabled={isExecuting}
                className={`bg-slate-100 hover:bg-slate-200 dark:bg-slate-800 dark:hover:bg-slate-750 text-slate-700 dark:text-slate-200 px-5 py-2.5 rounded-xl text-xs font-bold transition-all ${
                  isExecuting ? 'opacity-70 cursor-not-allowed' : 'cursor-pointer hover:-translate-y-0.5'
                }`}
              >
                Run Full Suite ({analysisResult.total_tests})
              </button>
            </div>
          </div>

          {/* Test Recommendations Accordion */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            
            {/* Recommended test list */}
            <div className="lg:col-span-2 space-y-4">
              <span className="font-bold text-slate-700 dark:text-slate-350 text-xs block uppercase tracking-wide">Recommended Test Suites</span>
              
              <div className="space-y-3">
                {analysisResult.recommended_tests.length === 0 ? (
                  <div className="border border-dashed border-slate-250 dark:border-slate-750 rounded-2xl py-12 text-center text-slate-400 italic">
                    {analysisResult.first_upload 
                      ? 'First version baseline registered. Subsequent version uploads will show recommended tests here.' 
                      : 'No tests recommended for the detected changes.'
                    }
                  </div>
                ) : (
                  analysisResult.recommended_tests.map((test, index) => (
                    <div key={index} className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl p-4.5 space-y-3 shadow-xs">
                      
                      {/* Top metadata line */}
                      <div className="flex flex-wrap items-center justify-between gap-2 text-xs">
                        <div className="flex items-center gap-2">
                          <span className={`text-[9px] font-black px-2 py-0.5 rounded-full ${IMPACT_LEVEL_STYLES[test.impact_level] || IMPACT_LEVEL_STYLES.LOW}`}>
                            {test.impact_level}
                          </span>
                          <span className="font-mono text-slate-700 dark:text-slate-350 font-bold bg-slate-50 dark:bg-slate-800 px-2 py-0.5 rounded text-[10px]">
                            {test.test_case_id}
                          </span>
                        </div>
                        <span className="text-[10px] text-slate-450 dark:text-slate-500 font-semibold bg-sky-50 dark:bg-sky-950/20 text-sky-600 dark:text-sky-400 px-2 py-0.5 rounded-full border border-sky-100 dark:border-sky-900/30">
                          {test.category}
                        </span>
                      </div>

                      {/* Title and component */}
                      <div>
                        <h4 className="font-bold text-slate-800 dark:text-white text-sm">{test.title}</h4>
                        <p className="text-[11px] text-slate-450 mt-1">Component: <strong className="text-slate-650 dark:text-slate-300 font-bold">{test.component}</strong> · Suite: <strong className="text-slate-650 dark:text-slate-300 font-mono font-medium">{test.test_file}</strong></p>
                      </div>

                      {/* Reason */}
                      <p className="text-[11px] leading-relaxed text-slate-500 dark:text-slate-450 bg-slate-50 dark:bg-slate-800/40 p-2.5 rounded-lg border border-slate-100 dark:border-slate-800 italic">
                        Recommendation Reason: {test.reason}
                      </p>

                      {/* Expandable Traceability details */}
                      {test.traceability && (
                        <div className="border border-slate-100 dark:border-slate-800/80 rounded-lg overflow-hidden bg-slate-50/50 dark:bg-slate-850/10">
                          <details className="group">
                            <summary className="flex items-center justify-between px-3 py-1.5 text-[10px] font-bold text-slate-550 dark:text-slate-400 cursor-pointer select-none">
                              <span className="uppercase tracking-wider flex items-center gap-1">
                                <Layers className="w-3.5 h-3.5 text-violet-500" />
                                Traceability Flow
                              </span>
                              <span className="transition-transform group-open:rotate-180">▼</span>
                            </summary>
                            <div className="p-3 border-t border-slate-100 dark:border-slate-800 bg-white dark:bg-slate-900 space-y-2.5 text-slate-650 dark:text-slate-400 text-xs">
                              <div className="flex flex-wrap items-center gap-2 text-[10px] font-bold text-slate-400">
                                <span className="text-slate-600 dark:text-slate-300">{test.traceability.changed_file}</span>
                                <ArrowRight className="w-3 h-3 text-slate-300" />
                                <span className="text-[#4318FF] dark:text-[#7357FF]">{test.traceability.component}</span>
                                <ArrowRight className="w-3 h-3 text-slate-300" />
                                <span className="text-amber-600 dark:text-amber-450">{test.traceability.ir_element}</span>
                                <ArrowRight className="w-3 h-3 text-slate-300" />
                                <span className="text-slate-650 dark:text-slate-300">{test.traceability.test_file}</span>
                              </div>
                              <div className="grid grid-cols-2 gap-2 text-[10px] bg-slate-50 dark:bg-slate-850/50 p-2 rounded border border-slate-100 dark:border-slate-800">
                                <div><span className="text-slate-400">Strategy ID:</span> <span className="font-mono">{test.traceability.strategy}</span></div>
                                <div><span className="text-slate-400">Edge Case ID:</span> <span className="font-mono">{test.traceability.edge_case}</span></div>
                              </div>
                            </div>
                          </details>
                        </div>
                      )}

                    </div>
                  ))
                )}
              </div>

              {/* Obsolete/Deleted Tests Warnings */}
              {analysisResult.deleted_components_traceability?.length > 0 && (
                <div className="space-y-3 pt-3">
                  <span className="font-bold text-red-500 text-xs block uppercase tracking-wide">
                    Obsolete / Deleted Components Warnings
                  </span>
                  <div className="space-y-2">
                    {analysisResult.deleted_components_traceability.map((del_step, del_idx) => (
                      <div key={del_idx} className="bg-red-50/20 dark:bg-red-950/10 border border-red-200/50 dark:border-red-900/35 rounded-xl p-4 flex gap-3 text-xs leading-relaxed text-slate-600 dark:text-slate-350">
                        <AlertTriangle className="w-4.5 h-4.5 text-red-500 shrink-0 mt-0.5" />
                        <div className="space-y-1">
                          <p>
                            A deletion was detected for component file: <strong className="font-mono text-slate-800 dark:text-slate-100">{del_step.changed_file}</strong>
                          </p>
                          <p className="text-slate-400 text-[11px]">
                            Associated test suite <strong className="font-mono text-slate-550 dark:text-slate-300">{del_step.test_file}</strong> (test case: <code className="font-mono">{del_step.test_case_id}</code>) has been flagged as obsolete. User review is recommended before removing test files.
                          </p>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>

            {/* Impact stats & reason summary */}
            <div className="space-y-4">
              <span className="font-bold text-slate-700 dark:text-slate-350 text-xs block uppercase tracking-wide">Analysis Breakdown</span>
              
              <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-5 space-y-4 shadow-xs">
                
                {/* Recommendation reasons aggregation */}
                <div>
                  <h4 className="font-bold text-xs uppercase tracking-wider text-slate-400 block mb-2">Explanations</h4>
                  <div className="space-y-2 max-h-56 overflow-y-auto pr-1 custom-scrollbar text-xs text-slate-650 dark:text-slate-350">
                    {analysisResult.reasons?.length === 0 ? (
                      <p className="text-xs text-slate-400 italic">No modifications detected.</p>
                    ) : (
                      analysisResult.reasons?.map((r, ri) => (
                        <div key={ri} className="flex gap-2 items-start py-0.5">
                          <span className="text-amber-500 font-extrabold shrink-0">•</span>
                          <p>{r}</p>
                        </div>
                      ))
                    )}
                  </div>
                </div>

                {/* Group levels summary */}
                <div className="border-t border-slate-100 dark:border-slate-800 pt-4 space-y-2 text-xs">
                  <h4 className="font-bold text-xs uppercase tracking-wider text-slate-400 block mb-2">Impact Count Breakdown</h4>
                  <div className="flex items-center justify-between">
                    <span className="text-slate-500 font-medium">HIGH Impact Cases</span>
                    <span className="font-bold text-red-500">{groupedRecommendations.HIGH.length}</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-slate-500 font-medium">MEDIUM Impact Cases</span>
                    <span className="font-bold text-amber-500">{groupedRecommendations.MEDIUM.length}</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-slate-500 font-medium">LOW Impact Cases</span>
                    <span className="font-bold text-sky-500">{groupedRecommendations.LOW.length}</span>
                  </div>
                </div>

              </div>
            </div>

          </div>

        </div>
      )}

      {/* Execution Progress & Results Display */}
      {isExecuting && (
        <div className="flex flex-col items-center justify-center py-16 gap-3">
          <RefreshCw className="w-8 h-8 text-amber-500 animate-spin" />
          <p className="text-sm font-semibold text-slate-600 dark:text-slate-300">Executing selected Jest test files...</p>
        </div>
      )}

      {executionError && (
        <div className="bg-red-50/50 border border-red-200 text-red-600 px-4 py-3 rounded-2xl text-xs font-semibold flex items-center gap-2">
          <AlertTriangle className="w-4 h-4 shrink-0" />
          {executionError}
        </div>
      )}

      {executionResult && (
        <div className="space-y-6 animate-in fade-in slide-in-from-bottom-2 duration-200">
          <div className="border border-slate-100 dark:border-slate-800 rounded-2xl p-5 bg-white dark:bg-slate-900 space-y-4">
            
            {/* Header info */}
            <div className="flex items-center justify-between border-b border-slate-100 dark:border-slate-800 pb-3">
              <div className="flex items-center gap-2">
                <CheckCircle className="w-5 h-5 text-emerald-500" />
                <h3 className="font-bold text-slate-900 dark:text-white text-base">Execution Finished</h3>
              </div>
              <span className="bg-emerald-100 text-emerald-800 text-[10px] font-extrabold px-3 py-1 rounded-full uppercase">
                {executionResult.status}
              </span>
            </div>

            {/* Run summaries */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-xs">
              <div className="bg-slate-50 dark:bg-slate-800/40 p-3.5 rounded-xl border border-slate-150 dark:border-slate-800/80">
                <span className="text-slate-400 block mb-0.5">Tests Run</span>
                <span className="text-lg font-bold text-slate-800 dark:text-slate-150">{executionResult.total_tests}</span>
              </div>
              <div className="bg-slate-50 dark:bg-slate-800/40 p-3.5 rounded-xl border border-slate-150 dark:border-slate-800/80">
                <span className="text-slate-400 block mb-0.5">Passed</span>
                <span className="text-lg font-bold text-emerald-600 dark:text-emerald-450">{executionResult.passed}</span>
              </div>
              <div className="bg-slate-50 dark:bg-slate-800/40 p-3.5 rounded-xl border border-slate-150 dark:border-slate-800/80">
                <span className="text-slate-400 block mb-0.5">Failed</span>
                <span className="text-lg font-bold text-red-500">{executionResult.failed}</span>
              </div>
              <div className="bg-slate-50 dark:bg-slate-800/40 p-3.5 rounded-xl border border-slate-150 dark:border-slate-800/80">
                <span className="text-slate-400 block mb-0.5">Pass Rate</span>
                <span className="text-lg font-bold text-slate-800 dark:text-slate-150">{executionResult.pass_rate}%</span>
              </div>
            </div>

            {/* Test files breakdown */}
            {executionResult.test_files?.length > 0 && (
              <div className="pt-2">
                <span className="font-bold text-slate-700 dark:text-slate-350 text-xs block uppercase tracking-wide mb-2">Selected Suite Execution Log</span>
                <div className="divide-y divide-slate-100 dark:divide-slate-850">
                  {executionResult.test_files.map((file, idx) => (
                    <div key={idx} className="py-2.5 flex items-center justify-between text-xs font-medium">
                      <div className="flex items-center gap-2">
                        {file.failed > 0 ? (
                          <span className="text-red-500 font-bold">✕</span>
                        ) : (
                          <span className="text-emerald-500 font-bold">✓</span>
                        )}
                        <span className="font-mono text-slate-800 dark:text-slate-150">{file.file_name}</span>
                      </div>
                      <span className={file.failed > 0 ? 'text-red-500 font-bold' : 'text-slate-500 font-medium'}>
                        {file.passed}/{file.total_tests} passed {file.failed > 0 && `(${file.failed} failed)`}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Failures breakdown */}
            {executionResult.failures?.length > 0 && (
              <div className="pt-2 space-y-3">
                <span className="font-bold text-red-700 dark:text-red-400 text-xs block uppercase tracking-wide">Failing assertions log</span>
                <div className="space-y-3">
                  {executionResult.failures.map((fail, idx) => (
                    <div key={idx} className="border border-red-200/50 dark:border-red-900/30 rounded-xl p-4 bg-red-50/5 dark:bg-red-950/5 space-y-2">
                      <div className="flex flex-wrap items-center justify-between gap-2 text-xs">
                        <div>
                          <strong className="text-slate-800 dark:text-slate-200">{fail.test_name}</strong>
                          <span className="text-slate-400 block text-[10px] mt-0.5">
                            File: {fail.file_name} {fail.line_number && `· Line ${fail.line_number}`}
                          </span>
                        </div>
                      </div>
                      <div className="bg-slate-900 text-[11px] font-mono text-red-400 rounded-lg p-3 overflow-x-auto whitespace-pre">
                        {fail.error_message}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

          </div>
        </div>
      )}

    </div>
  );
}
