import React, { Suspense, lazy } from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import DashboardLayout from '@/layouts/DashboardLayout';

// ─── Lazy-loaded pages ────────────────────────────────────────────────────────

const Dashboard = lazy(() => import('@/pages/Dashboard'));
const ProjectsPage = lazy(() => import('@/pages/ProjectsPage'));
const NewProjectPage = lazy(() => import('@/pages/NewProjectPage'));
const PromptManagement = lazy(() => import('@/pages/PromptManagement'));
const AppMain = lazy(() => import('@/App'));

// Helper page wrappers for tab views
const EpicsView: React.FC = () => <AppMain initialTab="blueprint" />;
const PipelineView: React.FC = () => <AppMain initialTab="generation" />;
const WorkspaceView: React.FC = () => <AppMain initialTab="workspace" />;
const TraceabilityView: React.FC = () => <AppMain initialTab="traceability" />;
const ValidationView: React.FC = () => <AppMain initialTab="validation" />;
const ApprovalsView: React.FC = () => <AppMain initialTab="review" />;
const ReportsView: React.FC = () => <AppMain initialTab="history" />;
const AuditView: React.FC = () => <AppMain initialTab="audit" />;

// ─── Page loading fallback ────────────────────────────────────────────────────

const PageLoader: React.FC = () => (
  <div className="p-6 max-w-[1600px] mx-auto space-y-6">
    {[...Array(3)].map((_, i) => (
      <div
        key={i}
        className="h-32 bg-gradient-to-r from-slate-100 via-slate-200 to-slate-100 bg-[length:200%_100%] animate-shimmer rounded-2xl"
      />
    ))}
  </div>
);

// ─── Routes ───────────────────────────────────────────────────────────────────

const AppRoutes: React.FC = () => (
  <Suspense fallback={<PageLoader />}>
    <Routes>
      <Route element={<DashboardLayout />}>
        <Route index element={<Dashboard />} />
        <Route path="projects" element={<ProjectsPage />} />
        <Route path="projects/new" element={<NewProjectPage />} />
        <Route path="epics" element={<EpicsView />} />
        <Route path="pipeline" element={<PipelineView />} />
        <Route path="workspace" element={<WorkspaceView />} />
        <Route path="artifacts" element={<WorkspaceView />} />
        <Route path="traceability" element={<TraceabilityView />} />
        <Route path="validation" element={<ValidationView />} />
        <Route path="approvals" element={<ApprovalsView />} />
        <Route path="reports" element={<ReportsView />} />
        <Route path="settings" element={<PromptManagement />} />
        <Route path="prompts" element={<PromptManagement />} />
        <Route path="audit" element={<AuditView />} />
        {/* Catch-all */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Route>
    </Routes>
  </Suspense>
);

export default AppRoutes;
