'use client';

import React, { useEffect, useState } from 'react';
import { useRouter, useParams } from 'next/navigation';
import {
  ChevronDown, ArrowRight, Loader2, CheckCircle2,
  FileText, Users, Settings, Link2, Target, AlertOctagon, ArrowLeft,
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { api } from '@/services/api';
import { ExtractedRequirementCategory } from '@/services/mockData';
import Link from 'next/link';

const CATEGORY_ICONS: Record<string, React.ComponentType<any>> = {
  'Actors & Personas':              Users,
  'Functional Requirements':        Settings,
  'Non-Functional Requirements':    CheckCircle2,
  'System Dependencies':            Link2,
  'Business Goals & Constraints':   Target,
  'Edge Cases':                     AlertOctagon,
};

const CATEGORY_COLORS: Record<string, string> = {
  'Actors & Personas':              'bg-blue-50 border-blue-200 text-blue-700',
  'Functional Requirements':        'bg-purple-50 border-purple-200 text-purple-700',
  'Non-Functional Requirements':    'bg-teal-50 border-teal-200 text-teal-700',
  'System Dependencies':            'bg-indigo-50 border-indigo-200 text-indigo-700',
  'Business Goals & Constraints':   'bg-orange-50 border-orange-200 text-orange-700',
  'Edge Cases':                     'bg-red-50 border-red-200 text-red-700',
};

const CATEGORY_BADGE: Record<string, string> = {
  'Actors & Personas':              'bg-blue-100 text-blue-700',
  'Functional Requirements':        'bg-purple-100 text-purple-700',
  'Non-Functional Requirements':    'bg-teal-100 text-teal-700',
  'System Dependencies':            'bg-indigo-100 text-indigo-700',
  'Business Goals & Constraints':   'bg-orange-100 text-orange-700',
  'Edge Cases':                     'bg-red-100 text-red-700',
};

export default function RequirementsPage({ projectId: propProjectId, onNavigate }: { projectId?: string; onNavigate?: (tab: string) => void } = {}) {
  const router    = useRouter();
  const params    = useParams();
  const projectId = propProjectId || (params?.projectId as string) || 'xbcxb';

  const [requirements, setRequirements] = useState<ExtractedRequirementCategory[]>([]);
  const [expandedIds, setExpandedIds]   = useState<Set<string>>(new Set());
  const [loading, setLoading]           = useState(true);
  const [error, setError]               = useState<string | null>(null);

  useEffect(() => {
    api
      .getRequirements(projectId)
      .then((data) => {
        setRequirements(data);
        // Auto-expand first two categories
        if (data.length > 0) setExpandedIds(new Set(data.slice(0, 2).map(d => d.id)));
        setLoading(false);
      })
      .catch((err) => {
        setError(err?.message || 'Failed to load requirements.');
        setLoading(false);
      });
  }, [projectId]);

  const toggleAccordion = (id: string) => {
    setExpandedIds((prev) => {
      const next = new Set(prev);
      next.has(id) ? next.delete(id) : next.add(id);
      return next;
    });
  };

  const totalItems = requirements.reduce((sum, c) => sum + c.items.length, 0);

  // ── Loading ──────────────────────────────────────────────────────────────────
  if (loading) {
    return (
      <div className="flex-1 flex flex-col min-h-screen bg-[#f8f9fc] font-sans">
        <div className="flex-1 flex items-center justify-center">
          <div className="flex flex-col items-center gap-3 text-gray-400">
            <Loader2 className="w-8 h-8 animate-spin text-[#ff5733]" />
            <p className="text-sm font-medium">Loading extracted requirements...</p>
          </div>
        </div>
      </div>
    );
  }

  // ── Error ────────────────────────────────────────────────────────────────────
  if (error && requirements.length === 0) {
    return (
      <div className="flex-1 flex flex-col min-h-screen bg-[#f8f9fc] font-sans items-center justify-center p-8">
        <div className="flex flex-col items-center gap-4 max-w-md text-center">
          <div className="w-14 h-14 rounded-2xl bg-red-50 border border-red-200 flex items-center justify-center">
            <AlertOctagon className="w-7 h-7 text-red-500" />
          </div>
          <h2 className="text-lg font-extrabold text-gray-900">Failed to Load Requirements</h2>
          <p className="text-sm text-gray-500">{error}</p>
          <button
            onClick={() => router.push(`/projects/${projectId}/processing`)}
            className="flex items-center gap-2 px-5 py-2.5 bg-gray-100 hover:bg-gray-200 text-gray-700 text-sm font-semibold rounded-xl transition-colors"
          >
            <ArrowLeft className="w-4 h-4" /> Back to Processing
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="w-full space-y-5 font-sans antialiased">
      {/* Title + stats row */}
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 tracking-tight">Extracted Requirements</h1>
          <p className="text-xs text-gray-500 mt-0.5">
            Review and approve the AI-extracted requirements before proceeding to epic generation.
          </p>
        </div>
      </div>

      {/* Summary Stats */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3.5 w-full">
        <div className="bg-white rounded-2xl border border-gray-200/80 shadow-xs p-5 space-y-1">
          <span className="text-[11px] font-bold text-gray-400 uppercase tracking-wider block">Total Items</span>
          <span className="text-2xl font-extrabold text-gray-900">{totalItems}</span>
        </div>
        <div className="bg-white rounded-2xl border border-gray-200/80 shadow-xs p-5 space-y-1">
          <span className="text-[11px] font-bold text-gray-400 uppercase tracking-wider block">Categories</span>
          <span className="text-2xl font-extrabold text-gray-900">{requirements.length}</span>
        </div>
        <div className="bg-white rounded-2xl border border-gray-200/80 shadow-xs p-5 space-y-1">
          <span className="text-[11px] font-bold text-gray-400 uppercase tracking-wider block">Pipeline Stage</span>
          <span className="text-base font-extrabold text-emerald-600 flex items-center gap-1.5 pt-1">
            <CheckCircle2 className="w-4 h-4" /> Completed
          </span>
        </div>
      </div>

      {/* Requirement Categories Accordion */}
      <div className="space-y-3 w-full">
        {requirements.map((category, catIdx) => {
          const isExpanded = expandedIds.has(category.id);
          const Icon       = CATEGORY_ICONS[category.title] || FileText;
          const colorCls   = CATEGORY_COLORS[category.title]  || 'bg-gray-50 border-gray-200 text-gray-700';
          const badgeCls   = CATEGORY_BADGE[category.title]   || 'bg-gray-100 text-gray-700';

          return (
            <div key={category.id} className="bg-white rounded-2xl border border-gray-200/80 shadow-xs overflow-hidden w-full">
              <button
                onClick={() => toggleAccordion(category.id)}
                className="w-full flex items-center justify-between p-5 hover:bg-gray-50/60 transition-colors focus:outline-none cursor-pointer"
              >
                <div className="flex items-center gap-4">
                  <div className={`w-9 h-9 rounded-xl border flex items-center justify-center shrink-0 ${colorCls}`}>
                    <Icon className="w-4 h-4" />
                  </div>
                  <div className="text-left">
                    <h3 className="font-bold text-gray-900 text-sm">{category.title}</h3>
                    <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full mt-0.5 inline-block ${badgeCls}`}>
                      {category.items.length} {category.items.length === 1 ? 'item' : 'items'}
                    </span>
                  </div>
                </div>
                <ChevronDown className={`w-4 h-4 text-gray-400 transition-transform duration-200 ${isExpanded ? 'rotate-180' : ''}`} />
              </button>

              <AnimatePresence initial={false}>
                {isExpanded && (
                  <motion.div
                    initial={{ height: 0, opacity: 0 }}
                    animate={{ height: 'auto', opacity: 1 }}
                    exit={{ height: 0, opacity: 0 }}
                    transition={{ duration: 0.2, ease: 'easeInOut' }}
                  >
                    <div className="border-t border-gray-100 bg-gray-50/40 px-6 py-4">
                      <ol className="space-y-2">
                        {category.items.map((item, idx) => (
                          <li key={idx} className="flex items-start gap-3">
                            <span className={`text-[10px] font-bold px-1.5 py-0.5 rounded shrink-0 mt-0.5 ${badgeCls}`}>
                              {String(catIdx * 100 + idx + 1).padStart(2, '0')}
                            </span>
                            <span className="text-xs text-gray-700 leading-relaxed font-medium">{item}</span>
                          </li>
                        ))}
                      </ol>
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>
            </div>
          );
        })}
      </div>

      {/* Bottom continue bar */}
      <div className="flex items-center justify-between p-5 bg-white rounded-2xl border border-gray-200/80 shadow-xs w-full">
        <div>
          <p className="text-sm font-bold text-gray-900">Ready to review epics?</p>
          <p className="text-xs text-gray-500 mt-0.5">
            Requirements look good — proceed to epic and feature review.
          </p>
        </div>
        <button
          onClick={() => onNavigate ? onNavigate('Outline / Epics') : router.push(`/projects/${projectId}/epics`)}
          className="flex items-center gap-2 px-6 py-2.5 bg-gradient-to-r from-[#FF602B] to-[#4318FF] text-white text-xs font-bold rounded-xl shadow-xs hover:opacity-95 transition-opacity cursor-pointer"
        >
          Continue to Epics <ArrowRight className="w-3.5 h-3.5" />
        </button>
      </div>

    </div>
  );
}
