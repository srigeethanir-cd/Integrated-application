# BA Accelerator Dashboard UI

Production-ready React + TypeScript + Tailwind dashboard for the AI Business Analyst & Engineering Accelerator platform.

## Location

This is the frontend application located at `backend/ui_dashboard/` (moved from root `frontend/`).

## Features

- **Fully API-driven** — all data consumed from `http://localhost:8000/api/v1/`
- **Real-time updates** — WebSocket connection + polling (5-15s intervals)
- **Premium SaaS design** — matches the reference UI exactly
- **Zero hardcoded values** — all dynamic from backend endpoints
- **Loading states** — skeleton loaders for every section
- **Error handling** — error states with retry functionality
- **Empty states** — when no data exists yet

## Tech Stack

- React 18.3.1
- TypeScript 5.4.5
- Vite 5.3.1 (build tool)
- Tailwind CSS 3.4.4
- React Router DOM 6.23.1
- Axios 1.7.2 (API client)
- date-fns 3.6.0 (date formatting)
- clsx 2.1.1 (className utility)

## Structure

```
src/
├── components/
│   ├── ui/              ← Badge, Card, Skeleton, ProgressBar, Button, etc.
│   ├── icons/           ← Inline SVG icons (zero dependencies)
│   ├── layout/          ← Sidebar, TopBar
│   └── dashboard/       ← HeroBanner, MetricCards, EpicsOverview, RecentActivity
├── hooks/
│   ├── useApi.ts        ← Generic polling hook
│   ├── useWebSocket.ts  ← WebSocket with auto-reconnect
│   └── useDashboard.ts  ← Domain-specific hooks (usePipelineStatus, useEpics, etc.)
├── services/
│   ├── types.ts         ← All TypeScript types
│   ├── apiClient.ts     ← Axios instance with interceptors
│   └── dashboardApi.ts  ← All API fetch functions
├── layouts/
│   └── DashboardLayout.tsx ← Root layout (Sidebar + TopBar + content)
├── pages/
│   ├── Dashboard.tsx    ← Main dashboard page
│   └── PlaceholderPage.tsx ← Stub for other routes
└── routes/
    └── AppRoutes.tsx    ← All route definitions
```

## API Endpoints Consumed

| Endpoint | Hook | Component |
|----------|------|-----------|
| `GET /api/v1/project/status` | `usePipelineStatus()` | HeroBanner, TopBar notifications |
| `GET /api/v1/projects/` | `useProjects()` | HeroBanner |
| `GET /api/v1/epics/` | `useEpics()` | EpicsOverview, Sidebar |
| `GET /api/v1/stories/` | `useStories()` | EpicsOverview, MetricCards |
| `GET /api/v1/files/` | `useGeneratedFiles()` | MetricCards |
| `GET /api/v1/reports/summary` | `useReportSummary()` | Reports page |
| `GET /api/v1/approval/status` | `useApprovalStatus()` | Sidebar, TopBar |
| `GET /api/v1/reports/generation-history` | `useRecentActivity()` | RecentActivity |
| `GET /api/v1/reports/story-audits` | `useRecentActivity()` | RecentActivity |

Plus aggregated hooks:
- `useDashboardSummary()` — computes totals from epics + stories + files
- `useEnrichedEpics()` — joins epics with story counts and progress

## Development

```bash
# Install dependencies
npm install

# Start dev server (with HMR)
npm run dev
# → http://localhost:5173

# Build for production
npm run build
# → outputs to dist/

# Preview production build
npm run preview
```

## Environment Variables

Create `.env` file (optional):

```env
VITE_API_BASE_URL=http://localhost:8000/api/v1
VITE_WS_BASE_URL=ws://localhost:8000/ws
```

Defaults are already set in the code if these are not provided.

## Vite Proxy

The `vite.config.ts` proxies `/api/*` requests to `http://localhost:8000` during development, so you can run the backend and frontend on different ports without CORS issues.

## Dashboard Sections

### 1. Hero Banner
- Current project name, ID, tech stack
- Overall progress percentage (0-100%)
- Status badge (Active, Running, Paused, etc.)
- Decorative SVG chart

### 2. Metric Cards (6 cards)
- Total Epics
- Total User Stories
- Completed Stories (with %)
- Pending Approval (needs review)
- In Progress (currently running)
- Generated Files

### 3. Epics Overview
- Horizontal scrollable card list
- Each card shows:
  - Circular progress (0-100%)
  - Story counts (Total, Completed, Pending)
  - Status badge (On Track, In Progress, Behind, Completed)

### 4. Recent Activity
- 5 most recent activity items from:
  - `generation_history` (Agent actions)
  - `story_audits` (State transitions)
- Each item shows icon, title, subtitle, timestamp

## Sidebar Navigation

- **Main**: Dashboard
- **Project Explorer**: Projects, Epics & Stories, AI Pipeline
- **Workspace**: Generation Workspace, Artifacts, Traceability
- **Quality & Approval**: Validation, Approvals, Reports
- **System**: Settings, Audit Logs

All routes render `PlaceholderPage.tsx` except `/` (Dashboard).

## TopBar

- Search bar (placeholder — search not yet implemented)
- Notifications panel (shows pending approvals + running workflows)
- "New Project" button

## Notes

- All components are **presentation-only** — no business logic in the UI
- State management is handled by React hooks (no Redux/Zustand)
- Polling intervals are tuned per endpoint (5s for pipeline, 10s for epics/stories, 30s for reports)
- WebSocket connection attempts auto-reconnect every 5s on disconnect
- Build output is optimized: 421 modules, ~3.6s build time, 247KB main bundle (gzipped: 82.72KB)

## Integration with Backend

The backend serves this UI from `/ui` when mounted as a static directory:

```python
# backend/main.py
app.mount("/ui", StaticFiles(directory="ui_dashboard/dist", html=True), name="static")
```

After building (`npm run build`), the `dist/` folder contains the production-ready static files.

Access the dashboard at: `http://localhost:8000/ui/`

## Future Enhancements

- Implement search functionality
- Add real-time push updates via WebSocket messages
- Build out all placeholder pages (Projects, Pipeline, Traceability, etc.)
- Add user authentication flow
- Implement "New Project" wizard
- Add export/download functionality for reports
