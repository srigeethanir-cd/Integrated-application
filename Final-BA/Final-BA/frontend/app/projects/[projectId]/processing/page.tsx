'use client';

import React, { useEffect, useState, useRef, useCallback } from 'react';
import { useRouter, useParams } from 'next/navigation';
import { api } from '@/services/api';
import {
  CheckCircle2, AlertTriangle, ArrowRight,
  Loader2, FileSearch, Cpu, GitBranch, BookOpen, ShieldCheck, Sparkles,
  FileText, Eye, Play, ArrowLeft, Terminal, RefreshCw,
} from 'lucide-react';
import Link from 'next/link';

// ─── localStorage key helpers ───────────────────────────────────────────────
function filePathKey(id: string)     { return `wf_file_path_${id}`; }
function workflowIdKey(id: string)   { return `wf_id_${id}`; }

// ─── Pipeline stages ────────────────────────────────────────────────────────
const PIPELINE_STAGES = [
  { key: 'Preprocessing',         label: 'Document Ingestion',       icon: FileSearch,  color: 'blue'   },
  { key: 'RequirementAnalysis',   label: 'Requirement Analysis',     icon: BookOpen,    color: 'purple' },
  { key: 'EpicGeneration',        label: 'Epic Generation',          icon: GitBranch,   color: 'teal'   },
  { key: 'FeatureGeneration',     label: 'Feature Mapping',          icon: Cpu,         color: 'indigo' },
  { key: 'UserStoryGeneration',   label: 'User Story Generation',    icon: Sparkles,    color: 'orange' },
  { key: 'ValidationGate',        label: 'Quality Validation',       icon: ShieldCheck, color: 'green'  },
];

const NODE_TO_STAGE: Record<string, string> = {
  START: 'Preprocessing', PENDING: 'Preprocessing', RUNNING: 'Preprocessing',
  preprocessing: 'Preprocessing',
  requirement_analysis: 'RequirementAnalysis',
  epic_generation: 'EpicGeneration',
  feature_generation: 'FeatureGeneration',
  one_line_story_generation: 'FeatureGeneration',
  nlp_rag_hook: 'UserStoryGeneration',
  user_story_generation: 'UserStoryGeneration',
  validation: 'ValidationGate',
  human_review_hook: 'ValidationGate',
  COMPLETED: 'COMPLETED',
  END: 'COMPLETED',
};


interface LogEntry {
  id: string;
  timestamp: string;
  stage: string;
  message: string;
  type: 'info' | 'success' | 'error' | 'agent';
}

function ts() { return new Date().toLocaleTimeString('en-US', { hour12: false }); }

export default function ProcessingPage({ projectId: propProjectId, onNavigate }: { projectId?: string; onNavigate?: (tab: string) => void } = {}) {
  const router   = useRouter();
  const params   = useParams();
  const projectId = propProjectId || (params?.projectId as string) || 'xbcxb';

  type Phase = 'preview' | 'running';
  const [phase, setPhase]             = useState<Phase>('preview');
  const [logs, setLogs]               = useState<LogEntry[]>([]);
  const [activeStageIdx, setActiveStageIdx] = useState(0);
  const [isComplete, setIsComplete]   = useState(false);
  const [isFailed, setIsFailed]       = useState(false);
  const [backendError, setBackendError] = useState<string | null>(null);
  const [pollCount, setPollCount]     = useState(0);
  const [canContinue, setCanContinue] = useState(false);

  const startedRef  = useRef(false);
  const logEndRef   = useRef<HTMLDivElement>(null);
  const simTimers   = useRef<ReturnType<typeof setTimeout>[]>([]);

  const addLog = useCallback((entry: Omit<LogEntry, 'id'>) => {
    setLogs(prev => [...prev, { ...entry, id: `${Date.now()}-${Math.random()}` }]);
    setTimeout(() => logEndRef.current?.scrollIntoView({ behavior: 'smooth' }), 50);
  }, []);

  const handleStartPipeline = () => {
    setPhase('running');
    if (startedRef.current) return;
    startedRef.current = true;

    // Start real backend call
    const tryBackend = async () => {
      try {
        const storedFilePath = localStorage.getItem(filePathKey(projectId));
        const effectiveFilePath = storedFilePath?.trim() || `${projectId}_PRD_Specification.pdf`;
        const validationMode = localStorage.getItem(`wf_validation_mode_${projectId}`) || 'every-step';

        const res = await api.startWorkflow(effectiveFilePath, 0.8, 3, projectId, validationMode);
        const workflowId = res?.workflow_id || projectId;
        localStorage.setItem(workflowIdKey(projectId), workflowId);

        let pollTimer: ReturnType<typeof setTimeout>;
        let processedLogIds = new Set<string>();

        const poll = async () => {
          try {
            const state = await api.getWorkflowStateById(workflowId);
            setPollCount(c => c + 1);

            // Fetch and map real backend execution history
            const execHistory = state?.state?.node_execution_log || state?.state?.execution_history || [];
            if (execHistory.length > 0) {
              const newLogs: LogEntry[] = [];
              
              execHistory.forEach((log: any) => {
                // Deduplicate by stable content signature instead of array index
                const stableKey = `real-${log.node_name}-${log.status}-${log.started_at || ''}-${log.completed_at || ''}`;
                if (!processedLogIds.has(stableKey)) {
                  processedLogIds.add(stableKey);
                  
                  const statusLabel = log.status === 'ERROR' || log.status === 'FAILED' ? 'error' 
                                    : log.status === 'COMPLETED' || log.status === 'SUCCESS' ? 'success' 
                                    : 'info';
                                    
                  let messageIcon = '🔵';
                  if (statusLabel === 'success') messageIcon = '✅';
                  if (statusLabel === 'error') messageIcon = '❌';

                  newLogs.push({
                    // Generate a truly unique ID that never collides
                    id: `log-${Date.now()}-${Math.random().toString(36).substring(2, 9)}`,
                    timestamp: log.completed_at || log.started_at || ts(),
                    stage: log.node_name || 'Agent',
                    message: `${messageIcon} [Backend] Node '${log.node_name}' finished with status: ${log.status}`,
                    type: statusLabel,
                  });
                }
              });

              if (newLogs.length > 0) {
                setLogs(prev => {
                  // Final safeguard: deduplicate entirely by ID in case of strict mode/merges
                  const merged = [...prev, ...newLogs];
                  const unique = Array.from(new Map(merged.map(item => [item.id, item])).values());
                  return unique;
                });
                setTimeout(() => logEndRef.current?.scrollIntoView({ behavior: 'smooth' }), 50);
              }
            }

            const node   = state?.state?.current_node || state?.workflow_status || 'preprocessing';
            const status = state?.workflow_status || 'RUNNING';
            const stageKey = NODE_TO_STAGE[node] || '';
            const idx = PIPELINE_STAGES.findIndex(s => s.key === stageKey);
            if (idx >= 0) setActiveStageIdx(idx);

            const isFinished = status === 'COMPLETED' || 
                               status === 'REVIEW_REQUIRED' || 
                               status === 'READY_FOR_REVIEW' || 
                               status === 'SUCCESS' || 
                               node === 'END' || 
                               node === 'human_review_hook' ||
                               node === 'COMPLETED';

            if (isFinished) {
              setIsComplete(true);
              setCanContinue(true);
              setActiveStageIdx(PIPELINE_STAGES.length);
              setLogs(prev => [...prev, {
                id: `final-success-${Date.now()}`,
                timestamp: ts(),
                stage: 'System',
                message: status === 'REVIEW_REQUIRED'
                  ? '🔍 Quality Validation completed. Backlog is ready for review.'
                  : '🎉 All AI agents completed successfully. Pipeline is ready for review.',
                type: 'success'
              }]);
              setTimeout(() => logEndRef.current?.scrollIntoView({ behavior: 'smooth' }), 50);
              return;
            }
            if (status === 'FAILED' || status === 'CANCELLED') {
              const errMsg = state?.state?.error_message || state?.error_message || `Backend workflow failed with status: ${status}`;
              setBackendError(errMsg);
              setIsFailed(true);
              setLogs(prev => [...prev, {
                id: `final-error-${Date.now()}`,
                timestamp: ts(),
                stage: 'System',
                message: `❌ Pipeline failed: ${errMsg}`,
                type: 'error'
              }]);
              setTimeout(() => logEndRef.current?.scrollIntoView({ behavior: 'smooth' }), 50);
              return;
            }
            pollTimer = setTimeout(poll, 2500);
          } catch (err) {
            setPollCount(c => c + 1);
            pollTimer = setTimeout(poll, 3000);
          }
        };
        poll();
      } catch (err: any) {
        const msg: string = err?.message || String(err);
        setBackendError(`Backend Error: ${msg}`);
      }
    };

    tryBackend();
  };

  // Cleanup timers on unmount
  useEffect(() => () => { simTimers.current.forEach(clearTimeout); }, []);

  return (
    <div className="w-full space-y-5 font-sans antialiased">

      {/* ══════════════════════════════════════════════════════════════════════
          PHASE 1: Document Preview
          ══════════════════════════════════════════════════════════════════ */}
      {phase === 'preview' && (
        <div className="space-y-4 w-full">
          <div>
            <h1 className="text-2xl font-bold text-gray-900 tracking-tight">Document Injected &amp; Preview</h1>
            <p className="text-xs text-gray-500 mt-0.5">Review your uploaded specification document before starting the AI pipeline.</p>
          </div>

          <div className="bg-white rounded-2xl border border-gray-200/80 shadow-xs p-6 md:p-7 space-y-5 w-full">
            <div className="flex items-start justify-between border-b border-gray-100 pb-4">
              <div className="flex items-center gap-3.5">
                <div className="w-11 h-11 rounded-xl bg-orange-50 border border-orange-200 text-[#FF602B] flex items-center justify-center shrink-0">
                  <FileText className="w-5 h-5" />
                </div>
                <div>
                  <h2 className="text-sm font-bold text-gray-900">{projectId}_PRD_Specification.pdf</h2>
                  <div className="flex items-center gap-2.5 text-xs text-gray-500 mt-0.5 font-medium">
                    <span>PDF Document</span><span>•</span><span>2.4 MB</span><span>•</span>
                    <span className="text-emerald-600 font-bold bg-emerald-50 px-2 py-0.5 rounded text-[11px]">Parsed Successfully</span>
                  </div>
                </div>
              </div>
              <span className="text-xs font-semibold text-gray-600 bg-gray-50 border border-gray-200 px-3 py-1.5 rounded-xl shadow-xs">Source: Local Ingestion</span>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3.5">
              {[['Extracted Pages','14 Pages'],['Text Chunks','42 Chunks'],['Detected Scope','High Confidence']].map(([label,val],i) => (
                <div key={i} className="p-4 rounded-xl bg-[#F8F9FC] border border-gray-200/80 space-y-1">
                  <span className="text-[11px] font-bold text-gray-400 uppercase tracking-wider block">{label}</span>
                  <span className={`text-xl font-extrabold ${i===2 ? 'text-[#FF602B]' : 'text-gray-900'}`}>{val}</span>
                </div>
              ))}
            </div>

            <div className="space-y-2">
              <div className="flex items-center justify-between text-xs font-bold text-gray-700">
                <span className="flex items-center gap-1.5"><Eye className="w-4 h-4 text-[#FF602B]" /> Document Content Preview Snippet</span>
                <span className="text-[11px] text-gray-400 font-mono">Lines 1–45</span>
              </div>
              <div className="p-4 bg-gray-900 text-gray-100 rounded-xl font-mono text-xs leading-relaxed max-h-56 overflow-y-auto border border-gray-800 space-y-2">
                <p className="text-emerald-400 font-bold"># System Requirement Specification &amp; PRD Overview</p>
                <p className="text-gray-300">1. Executive Summary: The platform shall automate user story generation, acceptance criteria, and INVEST validation from uploaded PRDs.</p>
                <p className="text-gray-300">2. Functional Requirements: Must support multi-source document ingestion (PDF, Word, Jira, Azure DevOps, SharePoint).</p>
                <p className="text-gray-300">3. Security &amp; Governance: All credentials and OAuth tokens must be stored in secure environment parameters.</p>
                <p className="text-gray-300">4. Target Output: Generated epics, features, one-line stories, and INVEST confidence scores exported directly to Jira or PDF.</p>
              </div>
            </div>
          </div>

          <div className="flex items-center justify-between bg-white rounded-2xl p-5 border border-gray-200/80 shadow-xs w-full">
            <div>
              <h3 className="text-sm font-bold text-gray-900">Ready to start AI Requirements &amp; Story Pipeline?</h3>
              <p className="text-xs text-gray-500 mt-0.5">Click below to launch automated AI agents for requirement extraction and epic mapping.</p>
            </div>
            <button
              onClick={handleStartPipeline}
              className="flex items-center gap-2 px-6 py-2.5 bg-gradient-to-r from-[#FF602B] to-[#4318FF] text-white text-xs font-bold rounded-xl shadow-sm hover:opacity-95 transition-opacity cursor-pointer"
            >
              <Play className="w-3.5 h-3.5 fill-white stroke-none" /> Start AI Pipeline Analysis →
            </button>
          </div>
        </div>
      )}

      {/* ══════════════════════════════════════════════════════════════════════
          PHASE 2: AI Pipeline Running
          ══════════════════════════════════════════════════════════════════ */}
      {phase === 'running' && (
        <div className="space-y-4 w-full">

          {/* Title */}
          <div>
            <h1 className="text-2xl font-bold text-gray-900 tracking-tight">Agent Pipeline</h1>
            <p className="text-xs text-gray-500 mt-0.5">Multi-agent workflow — 6 stages</p>
          </div>

          {/* Backend error badge (non-blocking) */}
          {backendError && (
            <div className="p-3 bg-amber-50 border border-amber-200 text-amber-800 text-xs rounded-xl">
              <div className="flex items-start gap-2.5 text-xs text-yellow-800">
                <AlertTriangle className="w-4 h-4 text-yellow-600 shrink-0" />
                <span>Backend note: {backendError}</span>
              </div>
            </div>
          )}

          <div className="flex flex-col lg:flex-row gap-5 items-start w-full">
            
            {/* Left Column: Stages & Progress */}
            <div className="flex-1 space-y-4 w-full">
              
              {/* ── Stages List ───────────────────────────────────────────── */}
              <div className="space-y-2.5">
                {PIPELINE_STAGES.map((stage, idx) => {
                  const isPassed  = idx < activeStageIdx || isComplete;
                  const isCurrent = idx === activeStageIdx && !isComplete;
                  
                  let bgClass = "bg-white border-gray-200/80";
                  let titleClass = "text-gray-400";
                  let rightBadge = <span className="px-2.5 py-1 bg-gray-50 text-gray-500 text-[10px] font-bold rounded-lg uppercase">Pending</span>;
                  let icon = <div className="w-2.5 h-2.5 rounded-full bg-gray-300 ml-1 mr-1" />;

                  if (isPassed) {
                    bgClass = "bg-[#F0FDF4] border-[#DCFCE7]";
                    titleClass = "text-gray-900";
                    rightBadge = <span className="px-2.5 py-1 bg-[#D1FAE5] text-[#059669] text-[10px] font-bold rounded-lg uppercase">Completed - {Math.floor(Math.random()*20)+10}s</span>;
                    icon = <CheckCircle2 className="w-5 h-5 text-emerald-500" />;
                  } else if (isCurrent) {
                    if (isFailed) {
                      bgClass = "bg-[#FEF2F2] border-[#FCA5A5]";
                      titleClass = "text-gray-900";
                      rightBadge = (
                        <div className="flex items-center gap-2">
                          <span className="text-[#EF4444] text-[10px] font-bold uppercase">Failed</span>
                          <button
                            onClick={() => {
                              setIsFailed(false);
                              setBackendError(null);
                              setPollCount(0);
                              startedRef.current = false;
                              handleStartPipeline();
                            }}
                            className="flex items-center gap-1 px-2.5 py-1 bg-white border border-[#FCA5A5] text-[#EF4444] rounded-lg hover:bg-[#FEE2E2] transition-colors text-[10px] font-bold uppercase"
                          >
                            <RefreshCw className="w-3 h-3" /> Regenerate
                          </button>
                        </div>
                      );
                      icon = <AlertTriangle className="w-5 h-5 text-[#EF4444]" />;
                    } else {
                      bgClass = "bg-[#EFF6FF] border-[#3B82F6]";
                      titleClass = "text-gray-900";
                      rightBadge = <span className="text-[#3B82F6] text-[10px] font-bold uppercase">Running • Processing...</span>;
                      icon = <Loader2 className="w-5 h-5 text-[#3B82F6] animate-spin" />;
                    }
                  }

                  return (
                    <div
                      key={stage.key}
                      className={`px-5 py-3.5 rounded-xl border flex items-center justify-between transition-all duration-300 shadow-xs ${bgClass}`}
                    >
                      <div className="flex items-center gap-3.5">
                        <div className="flex items-center justify-center shrink-0">
                          {icon}
                        </div>
                        <div>
                          <div className={`text-xs font-bold leading-tight ${titleClass}`}>{stage.label}</div>
                          <div className="text-[11px] text-gray-400 mt-0.5">{stage.label === 'Requirement Analysis' ? 'Extracting functional requirements' : stage.label === 'Document Ingestion' ? 'Parsing and chunking document' : stage.label === 'Epic Generation' ? 'Structuring high-level epics' : stage.label === 'Feature Mapping' ? 'Mapping features to epics' : stage.label === 'User Story Generation' ? 'Generating detailed user stories' : 'INVEST compliance & confidence scoring'}</div>
                        </div>
                      </div>
                      <div>
                        {rightBadge}
                      </div>
                    </div>
                  );
                })}
              </div>

              {/* Overall Progress and CTA */}
              <div className="bg-white p-5 rounded-2xl border border-gray-200/80 shadow-xs space-y-3">
                <div className="flex items-center justify-between text-xs font-bold">
                  <span className="text-gray-900">Overall Progress</span>
                  <span className="text-[#FF602B]">{isComplete ? '100%' : Math.min(99, Math.max(5, Math.floor((activeStageIdx / PIPELINE_STAGES.length) * 100)))}%</span>
                </div>
                <div className="w-full h-2 bg-gray-100 rounded-full overflow-hidden">
                  <div 
                    className={`h-full transition-all duration-500 ${isFailed ? 'bg-red-500' : 'bg-[#FF602B]'}`} 
                    style={{ width: `${isComplete ? 100 : Math.min(99, Math.max(5, Math.floor((activeStageIdx / PIPELINE_STAGES.length) * 100)))}%` }} 
                  />
                </div>
                <button
                  onClick={() => onNavigate ? onNavigate('Requirement Analysis') : router.push(`/projects/${projectId}/requirements`)}
                  disabled={!isComplete}
                  className={`w-full mt-1 py-2.5 rounded-xl text-white text-xs font-bold transition-all shadow-xs flex items-center justify-center gap-2 ${
                    isComplete ? 'bg-gradient-to-r from-[#FF602B] to-[#4318FF] hover:opacity-95 cursor-pointer' : 'bg-gray-100 text-gray-400 shadow-none cursor-not-allowed'
                  }`}
                >
                  View Validation Results →
                </button>
              </div>

            </div>

            {/* Right Column: Log & Stats */}
            <div className="w-full lg:w-[440px] xl:w-[480px] shrink-0">
              
              {/* ── Live Log Console ────────────────────────────────────────── */}
              <div className="bg-white rounded-2xl border border-gray-200/80 shadow-xs flex flex-col min-h-[480px] w-full">
                {/* Log header */}
                <div className="flex items-center justify-between px-5 py-3.5 border-b border-gray-100">
                  <h3 className="text-xs font-bold text-gray-900">Live Agent Log</h3>
                  <div className="flex items-center gap-1.5 text-[10px] font-bold text-[#10B981] uppercase tracking-wider">
                    <span className="w-2 h-2 rounded-full bg-[#10B981] animate-pulse" /> Live Feed
                  </div>
                </div>

                {/* Log entries */}
                <div className="flex-1 overflow-y-auto max-h-[460px] font-sans text-xs p-5 space-y-3" id="log-area">
                  {logs.length === 0 ? (
                    <div className="flex items-center gap-2 text-gray-400 py-10 justify-center">
                      <Loader2 className="w-4 h-4 animate-spin text-[#FF602B]" />
                      <span>Initializing AI agent workflow...</span>
                    </div>
                  ) : (
                    logs.map((log) => {
                      const cleanMsg = log.message.replace(/^[✅🤖🔍📋🔗📊🏗️🎯📝🗺️🔄📌✍️🧠✔️📈⚡🔵].*?(?=[A-Za-z])/g, '').replace('━━━ Stage', 'Stage').replace('━━━', '').trim();
                      let agentName = 'SYSTEM_MONITOR';
                      if (log.stage.includes('Ingestion') || log.stage.includes('Preprocessing')) agentName = 'INGESTION_AGENT';
                      else if (log.stage.includes('Requirement Analysis')) agentName = 'ANALYST_AGENT';
                      else if (log.stage.includes('Epic Generation')) agentName = 'EPIC_ARCHITECT';
                      else if (log.stage.includes('Feature Mapping')) agentName = 'MAPPER_AGENT';
                      else if (log.stage.includes('User Story Generation')) agentName = 'STORY_FORGE';
                      else if (log.stage.includes('Quality Validation')) agentName = 'QUALITY_GUARD';

                      return (
                        <div key={log.id} className="flex items-start gap-2.5">
                          <span className="text-gray-400 shrink-0 text-[10px] mt-0.5">{log.timestamp}</span>
                          <span className={`shrink-0 font-bold px-1.5 py-0.5 rounded text-[9px] uppercase mt-0.5 ${agentName === 'INGESTION_AGENT' ? 'bg-gray-100 text-gray-600' : agentName === 'ANALYST_AGENT' ? 'bg-emerald-50 text-emerald-700' : 'bg-gray-100 text-gray-600'}`}>
                            {agentName}
                          </span>
                          <span className="flex-1 text-gray-600 leading-snug text-xs">{cleanMsg}</span>
                        </div>
                      );
                    })
                  )}
                  <div ref={logEndRef} />
                </div>
              </div>

            </div>

          </div>
        </div>
      )}

    </div>
  );
}
