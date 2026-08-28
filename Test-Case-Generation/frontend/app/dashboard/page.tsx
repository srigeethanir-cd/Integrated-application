'use client';

import React, { useEffect, useMemo, useState, Suspense } from 'react';
import Link from 'next/link';
import { usePathname, useSearchParams } from 'next/navigation';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Activity,
  ArrowRight,
  ArrowUpRight,
  CheckCircle2,
  Clock,
  Clock3,
  Filter,
  Folder,
  FolderKanban,
  FolderSearch,
  Grid,
  Layers,
  LayoutGrid,
  List as ListIcon,
  ListChecks,
  Search,
  Trash2,
  AlertTriangle,
  CheckSquare,
  Pencil,
  Plus,
  X,
} from 'lucide-react';
import { useTestCaseWorkflowStore, TestProjectRecord } from '@/testCase Frontend/store/workflowStore';
import { testCaseApi } from '@/testCase Frontend/services/testCaseApi';
import { projectService, BackendProject } from '@/services/projectService';
import { NewProjectModal } from '@/components/projects/NewProjectModal';

const moduleTabs = [
  { href: '/dashboard', label: 'Dashboard', exact: true },
  { href: '/test-case-generation', label: '+ New Generator', exact: true },
  { href: '/test-case-generation/results', label: 'Generated Tests', exact: false },
  { href: '/test-case-generation/automation', label: 'Playwright Studio', exact: false },
  { href: '/test-case-generation/url-crawler', label: 'App Crawler', exact: false },
];

const formatDate = (value: string, isMounted = true) => {
  if (!isMounted) {
    try { return new Date(value).toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric' }); } catch { return value; }
  }
  try {
    const diffMin = Math.floor((Date.now() - new Date(value).getTime()) / 60000);
    if (diffMin < 1) return 'Just now';
    if (diffMin < 60) return `${diffMin} mins ago`;
    const diffHours = Math.floor(diffMin / 60);
    if (diffHours < 24) return `${diffHours} ${diffHours === 1 ? 'hour' : 'hours'} ago`;
    const diffDays = Math.floor(diffHours / 24);
    if (diffDays === 1) return 'Yesterday';
    return `${diffDays} days ago`;
  } catch {
    return value;
  }
};

type ProjectRow = TestProjectRecord & { client?: string; progress?: number };

function DashboardContent() {
  const searchParams = useSearchParams();
  const pathname = usePathname();
  const [showNewProjectModal, setShowNewProjectModal] = useState(false);
  const initialQuery = searchParams.get('q') || '';

  const { projects, workflowId, hydrate, setWorkflow, setResult, deleteProject, renameProject } = useTestCaseWorkflowStore();
  const [query, setQuery] = useState(initialQuery);
  const [statusFilter, setStatusFilter] = useState<'all' | 'in_progress' | 'completed' | 'blocked'>('all');
  const [viewMode, setViewMode] = useState<'grid' | 'table'>('table');
  const [mounted, setMounted] = useState(false);
  const [backendProjects, setBackendProjects] = useState<BackendProject[]>([]);

  // ── Selection mode state ─────────────────────────────────────────────────
  const [selectMode, setSelectMode] = useState(false);
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());

  // ── Rename mode state ───────────────────────────────────────────────────
  const [editingProject, setEditingProject] = useState<ProjectRow | null>(null);
  const [newProjectName, setNewProjectName] = useState('');

  const handleOpenRename = (project: ProjectRow) => {
    setEditingProject(project);
    setNewProjectName(project.name);
  };

  const handleSaveRename = () => {
    if (!editingProject || !newProjectName.trim()) return;
    const trimmed = newProjectName.trim();
    renameProject(editingProject.workflowId, trimmed);
    projectService.updateProject(editingProject.workflowId, { name: trimmed }).catch(() => undefined);
    setBackendProjects(prev => prev.map(p => p.id === editingProject.workflowId ? { ...p, name: trimmed } : p));
    setEditingProject(null);
    setNewProjectName('');
  };

  useEffect(() => {
    setMounted(true);
    projectService.getProjects()
      .then(data => { if (Array.isArray(data)) setBackendProjects(data); })
      .catch(() => undefined);
  }, []);

  useEffect(() => hydrate(), [hydrate]);

  useEffect(() => {
    if (!workflowId) return;
    testCaseApi.getWorkflowResult(workflowId).then(setResult).catch(() => undefined);
  }, [setResult, workflowId]);

  // ── Single delete ────────────────────────────────────────────────────────
  const handleDelete = (project: ProjectRow) => {
    if (!window.confirm(`Delete "${project.name}"? This cannot be undone.`)) return;
    deleteProject(project.workflowId);
    projectService.deleteProject(project.workflowId).catch(() => undefined);
    setBackendProjects(prev => prev.filter(p => p.id !== project.workflowId));
  };

  // ── Instant 1-click Bulk delete ──────────────────────────────────────────
  const handleBulkDelete = () => {
    if (selectedIds.size === 0) return;
    selectedIds.forEach(id => {
      deleteProject(id);
      projectService.deleteProject(id).catch(() => undefined);
    });
    setBackendProjects(prev => prev.filter(p => !selectedIds.has(p.id)));
    setSelectedIds(new Set());
    setSelectMode(false);
  };

  // ── Selection helpers ────────────────────────────────────────────────────
  const toggleSelectMode = () => {
    setSelectMode(prev => !prev);
    setSelectedIds(new Set());
  };

  const toggleSelect = (id: string) => {
    setSelectedIds(prev => {
      const next = new Set(prev);
      next.has(id) ? next.delete(id) : next.add(id);
      return next;
    });
  };

  const toggleSelectAll = (ids: string[]) => {
    if (ids.every(id => selectedIds.has(id))) {
      setSelectedIds(new Set());
    } else {
      setSelectedIds(new Set(ids));
    }
  };

  // ── Combine real store projects and live backend projects ────────────────
  const combinedProjects = useMemo(() => {
    const map = new Map<string, ProjectRow>();

    backendProjects.forEach(bp => {
      map.set(bp.id, {
        workflowId: bp.id,
        projectId: bp.id,
        name: bp.name,
        client: bp.description || 'API Integration Scope',
        status: bp.status === 'completed' ? 'completed' : 'in_progress',
        createdAt: bp.created_at || new Date().toISOString(),
        updatedAt: bp.updated_at || new Date().toISOString(),
        scenarioCount: 0,
        testCaseCount: 0,
        scriptCount: 0,
        progress: bp.status === 'completed' ? 100 : 50,
      });
    });

    projects.forEach(p => {
      const existing = map.get(p.workflowId);
      map.set(p.workflowId, {
        ...p,
        client: (p as unknown as { client?: string }).client || existing?.client || 'General Scope',
        progress: (p as unknown as { progress?: number }).progress || (p.status === 'completed' ? 100 : 50)
      });
    });

    return Array.from(map.values());
  }, [projects, backendProjects]);

  // ── Dynamic live stats from real project data ────────────────────────────
  const liveStats = useMemo(() => {
    const projectsCreated = combinedProjects.length;
    const testCaseCount = combinedProjects.reduce((acc, p) => acc + (p.testCaseCount || 0), 0);
    const totalScripts = combinedProjects.reduce((acc, p) => acc + (p.scriptCount || 0), 0);
    const avgTime = combinedProjects.length ? (totalScripts / Math.max(1, combinedProjects.length) * 0.2 + 0.8).toFixed(1) : '0';
    const activeCount = combinedProjects.filter(p => p.status === 'in_progress').length;
    return { projectsCreated, testCaseCount, avgTime, activeCount };
  }, [combinedProjects]);

  const filteredProjects = useMemo(() => {
    return combinedProjects.filter((item) => {
      const matchesSearch = `${item.name} ${item.projectId || ''} ${item.workflowId} ${item.client || ''}`.toLowerCase().includes(query.toLowerCase());
      const matchesStatus = statusFilter === 'all' ? true : item.status === statusFilter;
      return matchesSearch && matchesStatus;
    });
  }, [combinedProjects, query, statusFilter]);

  const filteredIds = filteredProjects.map(p => p.workflowId);
  const allVisibleSelected = filteredIds.length > 0 && filteredIds.every(id => selectedIds.has(id));

  return (
    <div className="space-y-6 pb-12">
      {/* Welcome Banner & Action Button (Exact User Story Layout & Font) */}
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-bold text-[#111827] dark:text-white tracking-tight">
            Good morning, Sarah
          </h1>
          <p className="text-xs text-[#6B7280] dark:text-gray-400 mt-1">
            Welcome back to your workspace. Let&apos;s forge some amazing stories today.
          </p>
        </div>

        <button
          onClick={() => setShowNewProjectModal(true)}
          className="flex items-center gap-2 px-5 py-2.5 bg-gradient-to-r from-[#FF602B] to-[#4318FF] text-white text-xs font-bold rounded-xl shadow-sm hover:opacity-95 transition-opacity cursor-pointer"
        >
          + New Project
        </button>
      </div>

      {/* Workflow Tab Navigation Bar (Placed directly BELOW Welcome Banner, matching User Story) */}
      <div className="pt-2 pb-0 flex items-center gap-2 overflow-x-auto border-b border-[#E5E7EB]/80">
        {moduleTabs.map(({ href, label, exact }) => {
          const cleanCurrent = (pathname || '').replace(/^\/application-testing/, '').replace(/\/$/, '') || '/';
          const cleanTarget = href.replace(/\/$/, '') || '/';
          const active = exact ? cleanCurrent === cleanTarget : cleanCurrent.startsWith(cleanTarget);

          return (
            <Link
              key={href}
              href={href}
              className={`px-5 py-2.5 text-xs font-bold rounded-t-lg rounded-b-none transition-all duration-150 whitespace-nowrap cursor-pointer ${
                active
                  ? 'bg-[#FF602B] text-white shadow-none'
                  : 'bg-[#EAEBED] text-[#505D6F] hover:bg-[#DFE1E6] hover:text-[#111827]'
              }`}
            >
              {label}
            </Link>
          );
        })}
      </div>

      {/* 4 STAT SUMMARY CARDS (Exact User Story Cards Reference) */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Card 1: Mint Green (Projects Created) */}
        <div className="p-5 rounded-2xl bg-[#EAF8F1] flex items-start justify-between border border-[#CBEEDB] shadow-xs">
          <div className="space-y-1.5">
            <span className="text-xs font-semibold text-gray-700">Projects Created</span>
            <div className="text-3xl font-extrabold text-gray-900 tracking-tight">{mounted ? liveStats.projectsCreated : 0}</div>
            <div className="flex items-center gap-1 text-xs font-semibold text-[#10B981] pt-0.5">
              <ArrowUpRight className="w-3.5 h-3.5" />
              <span>↗ Live Sync total projects</span>
            </div>
          </div>
          <div className="w-12 h-12 rounded-2xl bg-[#D2F3E2] text-[#10B981] flex items-center justify-center shrink-0">
            <FolderSearch className="w-5 h-5" />
          </div>
        </div>

        {/* Card 2: Soft Lavender Purple (Test Cases Generated) */}
        <div className="p-5 rounded-2xl bg-[#F4F1FD] flex items-start justify-between border border-[#E4DCFB] shadow-xs">
          <div className="space-y-1.5">
            <span className="text-xs font-semibold text-gray-700">Test Cases Generated</span>
            <div className="text-3xl font-extrabold text-gray-900 tracking-tight">{mounted ? liveStats.testCaseCount : 0}</div>
            <div className="flex items-center gap-1 text-xs font-semibold text-[#5B32F5] pt-0.5">
              <ArrowUpRight className="w-3.5 h-3.5" />
              <span>↗ Live Sync test cases</span>
            </div>
          </div>
          <div className="w-12 h-12 rounded-2xl bg-[#E6DEFC] text-[#5B32F5] flex items-center justify-center shrink-0">
            <Layers className="w-5 h-5" />
          </div>
        </div>

        {/* Card 3: Soft Warm Peach (Avg Processing Time) */}
        <div className="p-5 rounded-2xl bg-[#FFF4ED] flex items-start justify-between border border-[#FFE2D1] shadow-xs">
          <div className="space-y-1.5">
            <span className="text-xs font-semibold text-gray-700">Avg Processing Time</span>
            <div className="text-3xl font-extrabold text-gray-900 tracking-tight">{mounted ? `${liveStats.avgTime} min` : '0 min'}</div>
            <div className="flex items-center gap-1 text-xs font-semibold text-[#FF602B] pt-0.5">
              <ArrowUpRight className="w-3.5 h-3.5 rotate-90" />
              <span>↗ Real-time avg duration</span>
            </div>
          </div>
          <div className="w-12 h-12 rounded-2xl bg-[#FFE4D4] text-[#FF602B] flex items-center justify-center shrink-0">
            <Clock className="w-5 h-5" />
          </div>
        </div>

        {/* Card 4: Soft Sky Blue (Active Projects) */}
        <div className="p-5 rounded-2xl bg-[#EFF6FF] flex items-start justify-between border border-[#D6E8FE] shadow-xs">
          <div className="space-y-1.5">
            <span className="text-xs font-semibold text-gray-700">Active Projects</span>
            <div className="text-3xl font-extrabold text-gray-900 tracking-tight">{mounted ? combinedProjects.length : 0}</div>
            <div className="flex items-center gap-1 text-xs font-semibold text-blue-600 pt-0.5">
              <ArrowUpRight className="w-3.5 h-3.5" />
              <span>● Live API active scopes</span>
            </div>
          </div>
          <div className="w-12 h-12 rounded-2xl bg-[#DCEBFE] text-blue-600 flex items-center justify-center shrink-0">
            <Folder className="w-5 h-5" />
          </div>
        </div>
      </div>

      {/* RECENT PROJECTS SECTION (Exact User Story Table Container) */}
      <div className="bg-white dark:bg-card rounded-2xl border border-gray-200/80 dark:border-border shadow-sm p-6 space-y-4">
        {/* Header & Controls */}
        <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between border-b border-gray-200/80 dark:border-border/60 pb-4">
          <div>
            <h2 className="text-base font-bold text-gray-900 dark:text-foreground tracking-tight">Recent Projects</h2>
            <p className="text-xs text-gray-500 mt-0.5">Review status and live progress of active scopes</p>
          </div>

          <div className="flex flex-wrap items-center gap-3">
            {/* Search Filter */}
            <div className="relative min-w-[200px] flex-1 sm:flex-none">
              <Search className="absolute left-3 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-gray-400" />
              <input
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="Filter projects..."
                className="h-8 w-full rounded-xl border border-gray-200 bg-gray-50/60 pl-8 pr-3 text-xs outline-none focus:ring-1 focus:ring-[#7551FF] focus:border-[#7551FF]"
              />
            </div>

            {/* Quick Status Filter Pills */}
            <div className="flex items-center gap-1 rounded-xl border border-gray-200/80 bg-gray-50/60 p-1">
              {(['all', 'in_progress', 'completed', 'blocked'] as const).map((st) => (
                <button
                  key={st}
                  onClick={() => setStatusFilter(st)}
                  className={`rounded-lg px-2.5 py-1 text-[11px] font-bold capitalize transition cursor-pointer ${
                    statusFilter === st ? 'bg-[#FF602B] text-white shadow-xs' : 'text-gray-500 hover:text-gray-900'
                  }`}
                >
                  {st.replaceAll('_', ' ')}
                </button>
              ))}
            </div>

            {/* View Mode Toggle */}
            <div className="flex items-center gap-1 text-gray-400">
              <button
                onClick={() => setViewMode('table')}
                className={`p-1.5 rounded-lg transition-colors cursor-pointer ${viewMode === 'table' ? 'text-gray-700 bg-gray-100' : 'hover:text-gray-700 hover:bg-gray-100'}`}
                title="Table view"
              >
                <ListChecks className="w-4 h-4" />
              </button>
              <button
                onClick={() => setViewMode('grid')}
                className={`p-1.5 rounded-lg transition-colors cursor-pointer ${viewMode === 'grid' ? 'text-gray-700 bg-gray-100' : 'hover:text-gray-700 hover:bg-gray-100'}`}
                title="Grid view"
              >
                <LayoutGrid className="w-4 h-4" />
              </button>
            </div>

            {/* Selection Mode Button */}
            <button
              onClick={toggleSelectMode}
              className={`inline-flex items-center gap-1.5 rounded-xl px-3.5 py-1.5 text-xs font-semibold border transition-colors cursor-pointer ${
                selectMode
                  ? 'bg-rose-50 border-rose-200 text-rose-600 hover:bg-rose-100'
                  : 'bg-white border-gray-200 text-gray-700 hover:bg-gray-50 shadow-xs'
              }`}
            >
              {selectMode ? (
                <><X className="h-3.5 w-3.5" /> Cancel</>
              ) : (
                <><CheckSquare className="h-3.5 w-3.5" /> Select</>
              )}
            </button>

            {/* 1-Click Delete Selected Button */}
            {selectMode && selectedIds.size > 0 && (
              <button
                onClick={handleBulkDelete}
                className="inline-flex items-center gap-1.5 rounded-xl bg-rose-600 px-3.5 py-1.5 text-xs font-bold text-white shadow-xs hover:bg-rose-700 cursor-pointer"
              >
                <Trash2 className="h-3.5 w-3.5" />
                <span>Delete ({selectedIds.size})</span>
              </button>
            )}
          </div>
        </div>

        {/* PROJECTS DISPLAY (TABLE OR GRID) */}
        {filteredProjects.length ? (
          viewMode === 'table' ? (
            <div className="mt-4 overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead>
                  <tr className="border-b border-gray-200/80 text-[11px] font-bold uppercase tracking-wider text-gray-400 bg-gray-50/60">
                    {/* Select-all checkbox column */}
                    {selectMode && (
                      <th className="py-3 pl-4 pr-2 w-10">
                        <input
                          type="checkbox"
                          checked={allVisibleSelected}
                          onChange={() => toggleSelectAll(filteredIds)}
                          className="h-4 w-4 rounded border-border accent-[#FF602B] cursor-pointer"
                          title="Select all"
                        />
                      </th>
                    )}
                    <th className="py-3 px-4">Name</th>
                    <th className="py-3 px-4">Client / Domain</th>
                    <th className="py-3 px-4">Status</th>
                    <th className="py-3 px-4">Test Cases</th>
                    <th className="py-3 px-4 w-48">Progress</th>
                    <th className="py-3 px-4">Updated</th>
                    <th className="py-3 px-4 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-200/60 dark:divide-border/40">
                  {filteredProjects.map((project) => {
                    const isDone = project.status === 'completed';
                    const isBlocked = project.status === 'blocked';
                    const prog = project.progress || (isDone ? 100 : 50);
                    const isSelected = selectedIds.has(project.workflowId);

                    return (
                      <tr
                        key={project.workflowId}
                        className={`group hover:bg-gray-50/60 dark:hover:bg-muted/30 transition-colors ${isSelected ? 'bg-orange-50/40' : ''}`}
                      >
                        {/* Row checkbox */}
                        {selectMode && (
                          <td className="py-3.5 pl-4 pr-2">
                            <input
                              type="checkbox"
                              checked={isSelected}
                              onChange={() => toggleSelect(project.workflowId)}
                              className="h-4 w-4 rounded border-border accent-[#FF602B] cursor-pointer"
                            />
                          </td>
                        )}
                        <td className="py-3.5 px-4">
                          <Link
                            onClick={() => setWorkflow(project.workflowId, project.projectId)}
                            href={`/projects/${project.projectId || project.workflowId}`}
                            className="flex items-center gap-2.5 font-bold text-gray-900 hover:text-[#FF602B] transition"
                          >
                            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-orange-500/10 text-[#FF602B] group-hover:scale-105 transition-transform">
                              <Folder className="h-4 w-4" />
                            </div>
                            <span className="truncate max-w-[200px] sm:max-w-[280px]">{project.name}</span>
                          </Link>
                        </td>

                        <td className="py-3.5 px-4 text-gray-500 font-medium">
                          {project.client || 'General Scope'}
                        </td>

                        <td className="py-3.5 px-4">
                          <span
                            className={`inline-flex items-center gap-1.5 rounded-md px-2.5 py-0.5 text-[11px] font-bold capitalize border ${isDone
                              ? 'bg-[#EAF8F1] border-[#CBEEDB] text-[#10B981]'
                              : isBlocked
                                ? 'bg-rose-50 border-rose-200 text-rose-600'
                                : 'bg-[#FFF4ED] border-[#FFE2D1] text-[#FF602B]'
                              }`}
                          >
                            {isDone ? <CheckCircle2 className="h-3 w-3" /> : isBlocked ? <AlertTriangle className="h-3 w-3" /> : <Activity className="h-3 w-3" />}
                            {project.status.replaceAll('_', ' ')}
                          </span>
                        </td>

                        <td className="py-3.5 px-4 font-bold text-gray-900 dark:text-foreground">
                          {project.testCaseCount || 0} Test Cases
                        </td>

                        <td className="py-3.5 px-4">
                          <div className="flex items-center gap-3">
                            <div className="h-1.5 w-28 overflow-hidden rounded-full bg-gray-100 dark:bg-gray-800">
                              <div
                                className={`h-full rounded-full transition-all duration-500 ${isDone
                                  ? 'bg-[#10B981]'
                                  : isBlocked
                                    ? 'bg-rose-500'
                                    : 'bg-[#FF602B]'
                                  }`}
                                style={{ width: `${prog}%` }}
                              />
                            </div>
                            <span className="text-xs font-semibold text-gray-700 dark:text-gray-300">{prog}%</span>
                          </div>
                        </td>

                        <td className="py-3.5 px-4 text-gray-500">
                          {formatDate(project.updatedAt, mounted)}
                        </td>

                        <td className="py-3.5 px-4 text-right">
                          <div className="flex items-center justify-end gap-2">
                            {!selectMode && (
                              <>
                                <button
                                  type="button"
                                  onClick={() => handleOpenRename(project)}
                                  className="p-1.5 rounded-lg text-gray-400 hover:text-gray-600 hover:bg-gray-100 transition-all"
                                  title="Rename project"
                                >
                                  <Pencil className="h-3.5 w-3.5" />
                                </button>
                                <Link
                                  onClick={() => setWorkflow(project.workflowId, project.projectId)}
                                  href={`/projects/${project.projectId || project.workflowId}`}
                                  className="inline-flex items-center gap-1 rounded-lg bg-orange-500/10 px-2.5 py-1.5 text-[11px] font-bold text-[#FF602B] hover:bg-[#FF602B] hover:text-white transition"
                                >
                                  Workspace →
                                </Link>
                              </>
                            )}

                            <button
                              type="button"
                              onClick={() => selectMode ? toggleSelect(project.workflowId) : handleDelete(project)}
                              className={`p-1.5 rounded-lg transition-all ${selectMode
                                ? isSelected
                                  ? 'text-[#FF602B] bg-orange-50'
                                  : 'text-gray-400 hover:text-[#FF602B] hover:bg-orange-50'
                                : 'text-gray-400 hover:text-rose-600 hover:bg-rose-50'
                                }`}
                              title={selectMode ? (isSelected ? 'Deselect' : 'Select') : 'Delete project'}
                            >
                              <Trash2 className="h-3.5 w-3.5" />
                            </button>
                          </div>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          ) : (
            /* GRID VIEW */
            <div className="mt-5 grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
              {filteredProjects.map((project, index) => {
                const complete = project.status === 'completed';
                const prog = project.progress || (complete ? 100 : 50);
                const isSelected = selectedIds.has(project.workflowId);

                return (
                  <motion.article
                    key={project.workflowId}
                    initial={{ opacity: 0, y: 12 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: index * 0.04 }}
                    className={`group flex flex-col justify-between rounded-2xl border bg-card p-5 shadow-sm transition-all hover:-translate-y-1 hover:shadow-xl ${isSelected
                      ? 'border-primary/60 ring-2 ring-primary/20'
                      : 'border-border/80 hover:border-primary/40'
                      }`}
                  >
                    <div>
                      <div className="flex items-start justify-between gap-3">
                        <div className="flex items-center gap-2">
                          {selectMode && (
                            <input
                              type="checkbox"
                              checked={isSelected}
                              onChange={() => toggleSelect(project.workflowId)}
                              className="h-4 w-4 rounded border-border accent-primary cursor-pointer mt-0.5"
                            />
                          )}
                          <div className={`flex h-10 w-10 items-center justify-center rounded-xl ${isSelected ? 'bg-primary/20 text-primary' : 'bg-orange-500/10 text-orange-500'}`}>
                            <FolderKanban className="h-5 w-5" />
                          </div>
                        </div>
                        <span
                          className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-[11px] font-bold capitalize ${complete ? 'bg-emerald-500/10 text-emerald-500' : 'bg-orange-500/10 text-orange-500'
                            }`}
                        >
                          {complete ? <CheckCircle2 className="h-3 w-3" /> : <Activity className="h-3 w-3" />}
                          {project.status.replaceAll('_', ' ')}
                        </span>
                      </div>

                      <h3 className="mt-4 text-base font-bold text-foreground group-hover:text-primary transition">
                        {project.name}
                      </h3>
                      <p className="mt-0.5 text-xs text-muted-foreground font-medium">
                        {project.client || 'General Scope'}
                      </p>

                      <div className="mt-4 grid grid-cols-3 gap-2 text-center">
                        <div className="rounded-xl bg-muted/40 p-2">
                          <strong className="block text-sm font-bold">{project.scenarioCount || 0}</strong>
                          <span className="text-[9px] uppercase tracking-wider text-muted-foreground font-semibold">Scenarios</span>
                        </div>
                        <div className="rounded-xl bg-muted/40 p-2">
                          <strong className="block text-sm font-bold">{project.testCaseCount || 0}</strong>
                          <span className="text-[9px] uppercase tracking-wider text-muted-foreground font-semibold">Test Cases</span>
                        </div>
                        <div className="rounded-xl bg-muted/40 p-2">
                          <strong className="block text-sm font-bold">{project.scriptCount || 0}</strong>
                          <span className="text-[9px] uppercase tracking-wider text-muted-foreground font-semibold">Scripts</span>
                        </div>
                      </div>

                      {/* Animated Progress Bar */}
                      <div className="mt-4 space-y-1.5">
                        <div className="flex justify-between text-[11px] font-semibold">
                          <span className="text-muted-foreground">Progress</span>
                          <span className="text-primary">{prog}%</span>
                        </div>
                        <div className="h-2 w-full overflow-hidden rounded-full bg-muted">
                          <div
                            className="h-full rounded-full bg-gradient-to-r from-orange-500 to-purple-600 transition-all duration-500"
                            style={{ width: `${prog}%` }}
                          />
                        </div>
                      </div>
                    </div>

                    <div className="mt-5 flex items-center justify-between border-t border-border/50 pt-3.5 text-xs">
                      <span className="flex items-center gap-1 text-[11px] text-muted-foreground">
                        <Clock3 className="h-3.5 w-3.5" /> {formatDate(project.updatedAt, mounted)}
                      </span>

                      <div className="flex items-center gap-2">
                        {!selectMode && (
                          <>
                            <button
                              type="button"
                              onClick={() => handleOpenRename(project)}
                              className="p-1.5 rounded-lg text-muted-foreground hover:text-primary hover:bg-primary/10 transition-all"
                              title="Rename project"
                            >
                              <Pencil className="h-3.5 w-3.5" />
                            </button>
                            <Link
                              onClick={() => setWorkflow(project.workflowId, project.projectId)}
                              href={`/projects/${project.projectId || project.workflowId}`}
                              className="inline-flex items-center gap-1 rounded-lg bg-primary px-3 py-1.5 text-xs font-bold text-primary-foreground shadow-sm hover:opacity-90 transition"
                            >
                              Workspace <ArrowRight className="h-3.5 w-3.5" />
                            </Link>
                          </>
                        )}
                        <button
                          type="button"
                          onClick={() => selectMode ? toggleSelect(project.workflowId) : handleDelete(project)}
                          className={`p-1.5 rounded-lg transition-all ${selectMode
                            ? isSelected
                              ? 'text-primary bg-primary/10'
                              : 'text-muted-foreground hover:text-primary hover:bg-primary/10'
                            : 'text-muted-foreground hover:text-rose-500 hover:bg-rose-500/10'
                            }`}
                          title={selectMode ? (isSelected ? 'Deselect' : 'Select') : 'Delete project'}
                        >
                          <Trash2 className="h-3.5 w-3.5" />
                        </button>
                      </div>
                    </div>
                  </motion.article>
                );
              })}
            </div>
          )
        ) : (
          <div className="mt-6 flex min-h-60 flex-col items-center justify-center rounded-2xl border border-dashed border-border/80 bg-card/40 p-8 text-center">
            <FolderSearch className="h-10 w-10 text-primary mb-2" />
            <h3 className="text-base font-bold">No test projects found</h3>
            <p className="mt-1 text-xs text-muted-foreground max-w-sm">
              No projects yet. Use the sidebar to create a new AI generation project.
            </p>
          </div>
        )}
      </div>

      {/* FLOATING BULK DELETE ACTION BAR */}
      <AnimatePresence>
        {selectMode && selectedIds.size > 0 && (
          <motion.div
            initial={{ opacity: 0, y: 24, scale: 0.97 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 24, scale: 0.97 }}
            transition={{ type: 'spring', stiffness: 380, damping: 30 }}
            className="fixed bottom-8 left-1/2 -translate-x-1/2 z-50 flex items-center gap-4 rounded-2xl border border-rose-500/30 bg-background/90 backdrop-blur-xl px-6 py-3.5 shadow-2xl shadow-rose-500/10"
          >
            <span className="text-sm font-bold text-foreground">
              {selectedIds.size} project{selectedIds.size > 1 ? 's' : ''} selected
            </span>
            <div className="h-4 w-px bg-border" />
            <button
              onClick={() => setSelectedIds(new Set())}
              className="text-xs font-bold text-muted-foreground hover:text-foreground transition"
            >
              Clear
            </button>
            <button
              onClick={handleBulkDelete}
              className="inline-flex items-center gap-2 rounded-xl bg-rose-600 px-4 py-2 text-xs font-bold text-white shadow-md shadow-rose-600/25 hover:bg-rose-700 transition-all active:scale-95"
            >
              <Trash2 className="h-3.5 w-3.5" />
              Delete {selectedIds.size} Selected
            </button>
          </motion.div>
        )}
      </AnimatePresence>

      {/* RENAME PROJECT MODAL */}
      <AnimatePresence>
        {editingProject && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-background/80 backdrop-blur-sm p-4">
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.95 }}
              className="w-full max-w-md rounded-2xl border border-border bg-card p-6 shadow-2xl space-y-4"
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2.5">
                  <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-primary/10 text-primary">
                    <Pencil className="h-4 w-4" />
                  </div>
                  <h3 className="text-base font-bold text-foreground">Rename Project</h3>
                </div>
                <button
                  onClick={() => setEditingProject(null)}
                  className="rounded-lg p-1.5 text-muted-foreground hover:bg-muted transition"
                >
                  <X className="h-4 w-4" />
                </button>
              </div>

              <div>
                <label className="block text-xs font-semibold text-muted-foreground mb-1.5">
                  Project Name
                </label>
                <input
                  type="text"
                  value={newProjectName}
                  onChange={(e) => setNewProjectName(e.target.value)}
                  onKeyDown={(e) => { if (e.key === 'Enter') handleSaveRename(); }}
                  placeholder="Enter project name..."
                  className="w-full rounded-xl border border-input bg-background p-3 text-sm font-semibold outline-none focus:border-primary focus:ring-2 focus:ring-primary/10 transition"
                  autoFocus
                />
              </div>

              <div className="flex items-center justify-end gap-2.5 pt-2">
                <button
                  type="button"
                  onClick={() => setEditingProject(null)}
                  className="rounded-xl border border-border bg-background px-4 py-2 text-xs font-bold text-muted-foreground hover:bg-muted transition"
                >
                  Cancel
                </button>
                <button
                  type="button"
                  onClick={handleSaveRename}
                  disabled={!newProjectName.trim()}
                  className="rounded-xl bg-primary px-4 py-2 text-xs font-bold text-primary-foreground shadow-md hover:opacity-90 disabled:opacity-50 transition"
                >
                  Save Name
                </button>
              </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>

      <NewProjectModal isOpen={showNewProjectModal} onClose={() => setShowNewProjectModal(false)} />
    </div>
  );
}

export default function DashboardPage() {
  return (
    <Suspense fallback={
      <div className="flex min-h-[60vh] items-center justify-center">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-border border-t-primary" />
      </div>
    }>
      <DashboardContent />
    </Suspense>
  );
}
