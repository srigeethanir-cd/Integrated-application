import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'
import { AppShell } from './components/AppShell'
import { Dashboard, HistoryPage, ProcessingPage, ProjectRedirect, Projects, ReportsPage, SecurityReportPage, SettingsPage, TestCasesPage } from './pages/pages'
import { AppStateProvider } from './state/app-state'
import { RuntimeValidationPage } from './pages/RuntimeValidationPage'
import { AITestDetailsPage, AITestExplorerPage, AITestExportPage, AITestResultsOverview } from './pages/AITestResultsPages'

export default function App() {
  return <BrowserRouter basename="/backend-unit-testcase-generator"><AppStateProvider><Routes><Route element={<AppShell />}>
    <Route index element={<Dashboard />} />
    <Route path="projects" element={<Projects />} />
    <Route path="projects/:id" element={<ProjectRedirect />} />
    <Route path="processing/:id" element={<ProcessingPage />} />
    <Route path="ai-test-results/:id" element={<AITestResultsOverview />} />
    <Route path="ai-test-results/:id/tests" element={<AITestExplorerPage />} />
    <Route path="ai-test-results/:id/tests/:testId" element={<AITestDetailsPage />} />
    <Route path="ai-test-results/:id/export" element={<AITestExportPage />} />
    <Route path="security-report/:id" element={<SecurityReportPage />} />
    <Route path="runtime-validation/:id" element={<RuntimeValidationPage />} />
    <Route path="test-cases" element={<TestCasesPage />} />
    <Route path="reports" element={<ReportsPage />} />
    <Route path="history" element={<HistoryPage />} />
    <Route path="settings" element={<SettingsPage />} />
    <Route path="pipeline/*" element={<Navigate to="/test-cases" replace />} />
    <Route path="export" element={<Navigate to="/reports" replace />} />
    <Route path="*" element={<Navigate to="/" replace />} />
  </Route></Routes></AppStateProvider></BrowserRouter>
}
