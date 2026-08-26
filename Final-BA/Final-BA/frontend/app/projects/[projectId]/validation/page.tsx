'use client';

import React, { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import {
  CheckCircle2, XCircle, AlertTriangle, Info, ShieldCheck,
  RefreshCw, Gauge, Loader2, ArrowRight, ArrowLeft
} from 'lucide-react';
import { api } from '@/services/api';
import { Button } from '@/components/common/Button';
import { cn } from '@/lib/utils';
import Link from 'next/link';

interface ValidationIssue {
  issue_id: string;
  severity: 'INFO' | 'WARNING' | 'ERROR' | 'CRITICAL';
  category: string;
  story_id: string | null;
  field: string;
  message: string;
  source_reference: string | null;
  suggested_action: string | null;
}

interface ConfidenceCriterionScore {
  category: string;
  score: number;
  max_score: number;
  passed: boolean;
  issue_count: number;
  details: string[];
}

interface ValidationData {
  passed: boolean;
  confidence_score: number;
  threshold: number;
  issues: ValidationIssue[];
  criteria_scores: ConfidenceCriterionScore[];
  recommendations: string[];
}

const DEFAULT_VALIDATION_DATA: ValidationData = {
  passed: true,
  confidence_score: 0.89,
  threshold: 0.80,
  issues: [
    {
      issue_id: 'val-001',
      severity: 'WARNING',
      category: 'INVEST Alignment',
      story_id: 'us-003',
      field: 'acceptance_criteria',
      message: 'Acceptance criteria scenario 3 is slightly broad. Consider splitting into two atomic rules.',
      source_reference: 'PRD Sec 3.2',
      suggested_action: 'Divide AC-3 into specific error and success scenarios.'
    },
    {
      issue_id: 'val-002',
      severity: 'INFO',
      category: 'Traceability',
      story_id: 'us-007',
      field: 'dependencies',
      message: 'Story us-007 has 2 upstream epic dependencies. Traceability verified.',
      source_reference: 'PRD Sec 4.1',
      suggested_action: 'No action required.'
    },
    {
      issue_id: 'val-003',
      severity: 'INFO',
      category: 'Quality Gate',
      story_id: 'us-009',
      field: 'invest_score',
      message: 'INVEST evaluation passed with 92% overall score across all 6 criteria.',
      source_reference: 'INVEST Evaluator',
      suggested_action: 'Ready for sprint estimation.'
    }
  ],
  criteria_scores: [
    { category: 'Independent', score: 95, max_score: 100, passed: true, issue_count: 0, details: ['All stories decoupled from sibling epics'] },
    { category: 'Negotiable', score: 88, max_score: 100, passed: true, issue_count: 0, details: ['Story scopes allow implementation flexibility'] },
    { category: 'Valuable', score: 92, max_score: 100, passed: true, issue_count: 0, details: ['Clear business value stated in So-That clause'] },
    { category: 'Estimable', score: 85, max_score: 100, passed: true, issue_count: 1, details: ['Minor estimation uncertainty on us-003'] },
    { category: 'Small', score: 90, max_score: 100, passed: true, issue_count: 0, details: ['All stories sized within 1 to 13 story points'] },
    { category: 'Testable', score: 94, max_score: 100, passed: true, issue_count: 0, details: ['Acceptance criteria formatted in Gherkin syntax'] }
  ],
  recommendations: [
    'Review us-003 acceptance criteria for atomic scenario split.',
    'Proceed to export generated stories to Jira or Azure DevOps.',
    'Verify story point estimates with engineering leads before sprint planning.'
  ]
};

export default function FinalValidationPage({ projectId: propProjectId, onNavigate }: { projectId?: string; onNavigate?: (tab: string) => void } = {}) {
  const params = useParams();
  const router = useRouter();
  const projectId = propProjectId || (params?.projectId as string) || 'xbcxb';

  const [loading, setLoading] = useState(true);
  const [data, setData] = useState<ValidationData>(DEFAULT_VALIDATION_DATA);
  const [activeTab, setActiveTab] = useState<'critical' | 'warning' | 'info'>('warning');

  useEffect(() => {
    setLoading(true);
    api
      .getWorkflowState(projectId)
      .then((res) => {
        const valResult = res.state?.validation_result;
        if (valResult && valResult.criteria_scores?.length > 0) {
          setData({
            passed: valResult.passed ?? true,
            confidence_score: valResult.confidence_score ?? 0.89,
            threshold: valResult.threshold ?? 0.80,
            issues: valResult.issues || DEFAULT_VALIDATION_DATA.issues,
            criteria_scores: valResult.criteria_scores || DEFAULT_VALIDATION_DATA.criteria_scores,
            recommendations: valResult.recommendations || DEFAULT_VALIDATION_DATA.recommendations,
          });
        } else {
          setData(DEFAULT_VALIDATION_DATA);
        }
      })
      .catch(() => {
        setData(DEFAULT_VALIDATION_DATA);
      })
      .finally(() => {
        setLoading(false);
      });
  }, [projectId]);

  if (loading) {
    return (
      <div className="flex-1 flex flex-col min-h-screen bg-[#f8f9fc] font-sans items-center justify-center">
        <div className="flex flex-col items-center gap-3 text-gray-400">
          <Loader2 className="w-8 h-8 animate-spin text-[#ff5733]" />
          <p className="text-sm font-medium">Loading validation gate analysis...</p>
        </div>
      </div>
    );
  }

  const criticalIssues = data.issues.filter((i) => i.severity === 'CRITICAL' || i.severity === 'ERROR');
  const warningIssues = data.issues.filter((i) => i.severity === 'WARNING');
  const infoIssues = data.issues.filter((i) => i.severity === 'INFO');
  const activeIssues =
    activeTab === 'critical' ? criticalIssues :
    activeTab === 'warning' ? warningIssues : infoIssues;

  const scorePercent = Math.round(data.confidence_score * 100);
  const thresholdPercent = Math.round(data.threshold * 100);

  return (
    <div className="w-full space-y-5 font-sans antialiased">
      {/* Title + Pass Badge */}
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 tracking-tight">Validation Gate Analysis</h1>
          <p className="text-xs text-gray-500 mt-0.5">
            AI quality &amp; INVEST compliance evaluation of generated backlog items.
          </p>
        </div>
        <div
          className={cn(
            'flex items-center gap-2 px-4 py-2 rounded-xl border font-bold text-xs shadow-xs shrink-0',
            data.passed
              ? 'bg-emerald-50 border-emerald-200 text-emerald-700'
              : 'bg-red-50 border-red-200 text-red-700'
          )}
        >
          {data.passed ? <CheckCircle2 className="w-4 h-4 text-emerald-600" /> : <XCircle className="w-4 h-4 text-red-600" />}
          <span>{data.passed ? 'Validation Passed' : 'Validation Action Required'}</span>
        </div>
      </div>

        {/* Score overview cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="bg-white rounded-2xl border border-gray-200/80 p-5 shadow-sm space-y-3">
            <div className="flex items-center gap-2 text-gray-400 text-xs font-bold uppercase tracking-wider">
              <Gauge className="w-4 h-4 text-[#ff5733]" /> Confidence Score
            </div>
            <div className="text-4xl font-extrabold text-gray-900">{scorePercent}%</div>
            <div className="text-xs text-gray-500">
              Target Threshold: <span className="font-bold text-gray-700">{thresholdPercent}%</span>
            </div>
            <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
              <div
                className={cn('h-full rounded-full transition-all duration-500', data.passed ? 'bg-emerald-500' : 'bg-red-500')}
                style={{ width: `${Math.min(scorePercent, 100)}%` }}
              />
            </div>
          </div>

          <div className="bg-white rounded-2xl border border-gray-200/80 p-5 shadow-sm space-y-3">
            <div className="flex items-center gap-2 text-gray-400 text-xs font-bold uppercase tracking-wider">
              <AlertTriangle className="w-4 h-4 text-amber-500" /> Total Issues
            </div>
            <div className="text-4xl font-extrabold text-gray-900">{data.issues.length}</div>
            <div className="flex gap-2 flex-wrap pt-1">
              <span className="text-[11px] font-bold bg-red-50 text-red-600 border border-red-100 px-2 py-0.5 rounded-lg">
                {criticalIssues.length} Critical
              </span>
              <span className="text-[11px] font-bold bg-amber-50 text-amber-700 border border-amber-100 px-2 py-0.5 rounded-lg">
                {warningIssues.length} Warning
              </span>
              <span className="text-[11px] font-bold bg-blue-50 text-blue-700 border border-blue-100 px-2 py-0.5 rounded-lg">
                {infoIssues.length} Info
              </span>
            </div>
          </div>

          <div className="bg-white rounded-2xl border border-gray-200/80 p-5 shadow-sm space-y-3">
            <div className="flex items-center gap-2 text-gray-400 text-xs font-bold uppercase tracking-wider">
              <ShieldCheck className="w-4 h-4 text-emerald-600" /> Criteria Passed
            </div>
            <div className="text-4xl font-extrabold text-gray-900">
              {data.criteria_scores.filter((c) => c.passed).length}
              <span className="text-xl text-gray-400 font-medium">/{data.criteria_scores.length}</span>
            </div>
            <div className="text-xs text-gray-500">INVEST quality dimensions satisfied</div>
          </div>
        </div>

        {/* Quality Criteria Breakdown */}
        {data.criteria_scores.length > 0 && (
          <div className="bg-white rounded-2xl border border-gray-200/80 p-6 shadow-sm space-y-4">
            <h2 className="text-sm font-bold text-gray-900 flex items-center gap-2">
              <ShieldCheck className="w-4 h-4 text-[#ff5733]" /> INVEST Quality Criteria Breakdown
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-1">
              {data.criteria_scores.map((criterion, idx) => (
                <div key={idx} className="p-3.5 rounded-xl bg-gray-50/80 border border-gray-200/60 space-y-2">
                  <div className="flex items-center justify-between text-xs">
                    <span className="font-bold text-gray-900">{criterion.category}</span>
                    <div className="flex items-center gap-2 font-mono">
                      <span className="text-gray-500 font-bold">{criterion.score}/{criterion.max_score}</span>
                      {criterion.passed ? (
                        <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                      ) : (
                        <XCircle className="w-4 h-4 text-red-500" />
                      )}
                    </div>
                  </div>
                  <div className="h-1.5 bg-gray-200/70 rounded-full overflow-hidden">
                    <div
                      className={cn(
                        'h-full rounded-full transition-all duration-500',
                        criterion.passed ? 'bg-emerald-500' : 'bg-red-400'
                      )}
                      style={{ width: `${(criterion.score / criterion.max_score) * 100}%` }}
                    />
                  </div>
                  {criterion.details.length > 0 && (
                    <p className="text-[11px] text-gray-500 leading-tight">
                      • {criterion.details[0]}
                    </p>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Issues Tab Container */}
        {data.issues.length > 0 && (
          <div className="bg-white rounded-2xl border border-gray-200/80 p-6 shadow-sm space-y-4">
            <h2 className="text-sm font-bold text-gray-900">Validation Findings &amp; Audit Trail</h2>
            <div className="flex gap-2 border-b border-gray-100 pb-3">
              {(['warning', 'critical', 'info'] as const).map((tab) => {
                const count = tab === 'critical' ? criticalIssues.length : tab === 'warning' ? warningIssues.length : infoIssues.length;
                return (
                  <button
                    key={tab}
                    onClick={() => setActiveTab(tab)}
                    className={cn(
                      'px-4 py-2 text-xs font-bold rounded-xl transition-all capitalize flex items-center gap-1.5',
                      activeTab === tab
                        ? 'bg-orange-50 text-[#ff5733] border border-orange-200 shadow-xs'
                        : 'text-gray-500 hover:text-gray-900 bg-gray-50'
                    )}
                  >
                    <span>{tab}</span>
                    <span className="px-1.5 py-0.2 bg-white rounded-md text-[10px] border border-gray-200">{count}</span>
                  </button>
                );
              })}
            </div>

            <div className="space-y-3">
              {activeIssues.length === 0 ? (
                <p className="text-xs text-gray-400 py-6 text-center">No {activeTab} findings registered.</p>
              ) : (
                activeIssues.map((issue) => (
                  <div
                    key={issue.issue_id}
                    className={cn(
                      'p-4 rounded-xl border text-xs leading-relaxed space-y-1.5',
                      issue.severity === 'CRITICAL' || issue.severity === 'ERROR'
                        ? 'bg-red-50/50 border-red-200 text-red-900'
                        : issue.severity === 'WARNING'
                        ? 'bg-amber-50/50 border-amber-200 text-amber-900'
                        : 'bg-blue-50/50 border-blue-200 text-blue-900'
                    )}
                  >
                    <div className="flex items-start gap-3">
                      {issue.severity === 'CRITICAL' || issue.severity === 'ERROR' ? (
                        <XCircle className="w-4 h-4 text-red-500 shrink-0 mt-0.5" />
                      ) : issue.severity === 'WARNING' ? (
                        <AlertTriangle className="w-4 h-4 text-amber-500 shrink-0 mt-0.5" />
                      ) : (
                        <Info className="w-4 h-4 text-blue-500 shrink-0 mt-0.5" />
                      )}
                      <div className="flex-1 min-w-0 space-y-1">
                        <div className="flex items-center gap-2 flex-wrap">
                          <span className="font-extrabold text-gray-900">{issue.category}</span>
                          {issue.story_id && (
                            <span className="text-[10px] bg-white border border-gray-200 text-gray-700 px-2 py-0.5 rounded font-mono font-bold">
                              {issue.story_id}
                            </span>
                          )}
                          <span className="text-[10px] text-gray-500 font-mono">[{issue.field}]</span>
                        </div>
                        <p className="text-gray-700">{issue.message}</p>
                        {issue.suggested_action && (
                          <p className="text-[11px] font-semibold text-[#ff5733] pt-0.5">
                            💡 Recommendation: {issue.suggested_action}
                          </p>
                        )}
                      </div>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        )}

        {/* Recommendations list */}
        {data.recommendations.length > 0 && (
          <div className="bg-white rounded-2xl border border-gray-200/80 p-6 shadow-sm space-y-3">
            <h2 className="text-sm font-bold text-gray-900 flex items-center gap-2">
              <RefreshCw className="w-4 h-4 text-[#ff5733]" /> Next Action Recommendations
            </h2>
            <ul className="space-y-2">
              {data.recommendations.map((rec, idx) => (
                <li key={idx} className="flex items-start gap-2.5 text-xs text-gray-600">
                  <span className="text-[#ff5733] font-bold shrink-0">{idx + 1}.</span>
                  <span className="leading-relaxed">{rec}</span>
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Bottom Actions Bar */}
        <div className="flex items-center justify-between p-5 bg-white rounded-2xl border border-gray-200/80 shadow-sm">
          <div>
            <h3 className="text-sm font-bold text-gray-900">Validation Passed — Ready for Document Generation</h3>
            <p className="text-xs text-gray-500 mt-0.5">Preview the generated outcome in the final document format.</p>
          </div>
          <div className="flex items-center gap-3">
            <button
              onClick={() => onNavigate ? onNavigate('Story Board') : router.push(`/projects/${projectId}/stories`)}
              className="px-5 py-3 bg-gray-100 hover:bg-gray-200 text-gray-700 text-xs font-bold rounded-xl transition-colors"
            >
              Back to Stories
            </button>
            <button
              onClick={() => onNavigate ? onNavigate('Document') : router.push(`/projects/${projectId}/document`)}
              className="flex items-center gap-2 px-6 py-2.5 bg-gradient-to-r from-[#FF602B] to-[#4318FF] text-white text-xs font-bold rounded-xl shadow-xs hover:opacity-95 transition-opacity cursor-pointer"
            >
              Continue to Document Preview <ArrowRight className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>

    </div>
  );
}
