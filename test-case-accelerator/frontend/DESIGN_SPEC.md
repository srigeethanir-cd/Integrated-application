# Test Case Accelerator — Production UI/UX Specification

## 1. Product frame

Desktop application shell:

```text
┌────────────── 248px ──────────────┬──────────────────────────────────────────────┐
│ Product mark                      │ Header, 64px                                  │
│                                   ├───────────────────────────────────────────────┤
│ Overview                          │                                               │
│ Projects                          │ Main content                                  │
│ Pipeline                          │ max-width: 1440px                              │
│   Dependency Analysis             │ padding: 40px                                 │
│   Code Understanding              │                                               │
│   Test Generation                 │                                               │
│   Test Verification               │                                               │
│   Coverage & Quality              │                                               │
│ Export                            │                                               │
│ Settings                          │                                               │
│                                   │                                               │
│ Runtime Validation  Coming Soon   │                                               │
└───────────────────────────────────┴───────────────────────────────────────────────┘
```

- Light theme is the production default.
- Sidebar and header remain fixed; only the content canvas scrolls.
- Content width is fluid from 1024px to 1440px.
- No screen displays data that cannot be derived from an existing response or current-session request state.
- No authentication, notification, runtime-validation, server-side export, or persisted-settings behavior is implied.

## 2. Existing backend contract map

| UI capability | Existing endpoint | Data used |
|---|---|---|
| Health status | `GET /health` | health response |
| Project selector/list | `GET /projects?skip=&limit=` | `items`, `total` |
| Project detail | `GET /projects/{project_id}` | complete `ProjectResponse` |
| Upload project | `POST /projects/upload` | multipart project fields |
| Import GitHub project | `POST /projects/github` | name, description, `github_url` |
| Delete project | `DELETE /projects/{project_id}` | HTTP status |
| Full upload workflow | `POST /workflows/upload` | `project`, `dependency`, `pipeline` |
| Full GitHub workflow | `POST /workflows/github` | `project`, `dependency`, `pipeline` |
| Dependency analysis | `POST /projects/{project_id}/dependencies` | `run_id`, `status` |
| Dependency result | `GET /dependency-runs/{run_id}` | project, status, `files` |
| Code understanding | `POST /projects/{project_id}/understand` | Stage 3 result |
| Integrated pipeline | `POST /projects/{project_id}/pipeline` | Stage 3–6 result |
| Test generation | `POST /projects/{project_id}/generate-test-cases` | generated cases and coverage |
| Test verification | `POST /projects/{project_id}/verify-test-cases` | results and summary |
| Quality evaluation | `POST /projects/{project_id}/evaluate-test-quality` | score, dimensions, feedback, plan |
| Quality optimization | `POST /projects/{project_id}/optimize-test-quality` | complete loop result |

Run IDs and stage artifacts returned during a workflow are retained in client state for the active browser session. The backend has no list endpoint for code-understanding runs; the UI must not suggest historical run retrieval.

## 3. Route architecture

```text
/
/projects
/projects/:projectId
/pipeline
/pipeline/dependencies
/pipeline/understanding
/pipeline/generation
/pipeline/verification
/pipeline/quality
/export
/settings
```

`Runtime Validation` is rendered as a disabled navigation item and has no route.

## 4. Global application shell

### Sidebar specification

- Width: 248px desktop; 72px compact desktop; drawer on mobile.
- Background: `#FFFFFF`.
- Right border: 1px `#E5E7EB`.
- Product row: 64px high, 20px horizontal padding.
- Navigation begins 20px below product row.
- Section gap: 24px. Item gap: 4px.
- Item: 40px high, 10px radius, 12px horizontal padding.
- Icon: Lucide, 18px, 1.75 stroke.
- Default text: `#4B5563`; hover: `#111827` on `#F8FAFC`.
- Active item: `#075985` text/icon on `#F0F9FF`; no left color bar.
- Pipeline children: 36px high, 42px left padding, 14px type.
- `Runtime Validation` uses `aria-disabled=true`, `#9CA3AF`, no pointer action.
- `Coming Soon` badge: 11px/16px, `#F3F4F6`, `#6B7280`, 6px radius.

```text
┌────────────────────────────┐
│ ◇  Test Case Accelerator   │
├────────────────────────────┤
│ ▣  Overview                │
│ □  Projects                │
│ ▶  Pipeline                │
│    Dependency Analysis     │
│    Code Understanding      │
│    Test Generation         │
│    Test Verification       │
│    Coverage & Quality      │
│ ⇩  Export                  │
│ ⚙  Settings                │
│                            │
│ ◷  Runtime Validation      │
│       [Coming Soon]        │
└────────────────────────────┘
```

### Header specification

- Height: 64px; white background; bottom border `#E5E7EB`.
- Horizontal padding: 24px.
- Left: project selector, 240px.
- Center: search, max 420px. Search filters the currently loaded table/client data only.
- Right: notification icon, theme toggle, profile affordance, primary upload button.
- Notification icon reports current-session request completion/errors only; no unread server count.
- Profile is a neutral avatar/menu shell with no account fields because no auth/profile API exists.
- Theme toggle stores preference locally; it never calls the backend.
- Exactly one primary action: `Upload Project`.

```text
┌──────────────────────────────────────────────────────────────────────────────┐
│ [Project: Acme API ▾]    [⌕ Search current view…          ]  🔔  ☼  KR  [Upload Project] │
└──────────────────────────────────────────────────────────────────────────────┘
```

Project selector data comes from `GET /projects`. Selecting a project sets active client context; it does not mutate backend data.

## 5. Page wireframes

### 5.1 Overview

Data source: active workflow/pipeline response plus `GET /projects`. If no workflow has run in the current session, stage metrics show `—`, never fabricated zeroes.

```text
Overview
Monitor the active project's test-generation pipeline.

┌──────────────────────────────── Pipeline status ─────────────────────────────┐
│  ✓ Upload ── ✓ Dependency ── ● Understanding ── ○ Generation ── ○ Verification │
│                                                     Current: Understanding     │
└───────────────────────────────────────────────────────────────────────────────┘

┌──────────────────┐ ┌──────────────────┐ ┌──────────────────┐ ┌──────────────────┐
│ Coverage         │ │ Quality score    │ │ Generated tests  │ │ Verified tests   │
│ 88.9%            │ │ 85 / 100         │ │ 24               │ │ 19               │
│ Category coverage│ │ Threshold met    │ │ After dedupe      │ │ 3 partial, 2 fail│
└──────────────────┘ └──────────────────┘ └──────────────────┘ └──────────────────┘

Recent projects
┌───────────────────────────────────────────────────────────────────────────────┐
│ Project              Source      Status       Updated                         │
│ Payments API         GitHub      Ready        2 hours ago                     │
│ Customer service     ZIP         Uploaded     Yesterday                       │
└───────────────────────────────────────────────────────────────────────────────┘

Recent activity
┌───────────────────────────────────────────────────────────────────────────────┐
│ 10:42  Verification completed       19 verified                              │
│ 10:39  Test generation completed    24 test cases                            │
└───────────────────────────────────────────────────────────────────────────────┘
```

Mappings:

- Coverage: `test_generation.coverage_summary.category_coverage`.
- Quality: `quality_evaluation.overall_score` or `final_score`.
- Generated: `total_after_deduplication`.
- Verified: `test_verification.summary.verified`.
- Current stage: inferred only from current-session completed responses/statuses.
- Recent projects: first five `ProjectListResponse.items` sorted as returned.
- Recent activity: current-session request lifecycle only; clear on reload.
- Use one thin progress bar for coverage. No decorative charts.

### 5.2 Projects

```text
Projects                                                    [Upload Project]
Manage uploaded and GitHub-backed codebases.

[⌕ Search projects…] [Source ▾] [Status ▾]                  11 projects
┌───────────────────────────────────────────────────────────────────────────────┐
│ Project              Source       Status       Updated          Actions       │
│ Customer API         ZIP          Ready        Jul 21, 2026     View    ⋯      │
│ Billing service      GitHub       Ready        Jul 20, 2026     View    ⋯      │
│ Inventory API        ZIP          Uploaded     Jul 18, 2026     View    ⋯      │
├───────────────────────────────────────────────────────────────────────────────┤
│ Showing 1–10 of 11                            ‹ Previous  1  2  Next ›         │
└───────────────────────────────────────────────────────────────────────────────┘
```

- Source filter uses `source_type` already loaded.
- Status filter uses `status` already loaded.
- Pagination calls `GET /projects?skip={n}&limit={n}`.
- Row action `View` opens `/projects/:id` and calls `GET /projects/{id}`.
- Overflow contains only `Delete`; confirmation names the project and calls existing DELETE.
- No edit action: no project update endpoint exists.

Upload modal:

```text
Upload project                                             ×
Add a ZIP archive or import a public GitHub repository.

[ ZIP Upload ] [ GitHub ]

Project name       [                                      ]
Description        [                                      ]
Archive            [ Choose .zip file                     ]

                                      [Cancel] [Upload Project]
```

- ZIP tab maps to `POST /projects/upload`.
- GitHub tab replaces Archive with HTTPS GitHub URL and maps to `POST /projects/github`.
- Optional `Run complete pipeline after upload` is not shown: it would ambiguously choose between project and workflow APIs. Full workflow begins from the Pipeline page.

### 5.3 Project detail

```text
← Projects
Customer API                                      [Ready]
Uploaded ZIP project · Updated Jul 21, 2026

┌──────────────────────────────┐ ┌─────────────────────────────────────────────┐
│ Project details              │ │ Start analysis                              │
│ ID          057e…603e        │ │ Run dependency analysis for this project.   │
│ Source      ZIP              │ │                         [Analyze Project]   │
│ Created     Jul 21, 2026     │ └─────────────────────────────────────────────┘
│ Storage     …/projects/057e  │
└──────────────────────────────┘
```

- Detail data maps exactly to `ProjectResponse`.
- `Analyze Project` calls Stage 2 and routes to Dependency Analysis with returned `run_id`.
- GitHub URL appears only when non-null.
- Storage path uses monospace caption and copy control.

### 5.4 Pipeline hub

```text
Pipeline
Run and inspect each implemented analysis stage.

┌───────────────────────────────────────────────────────────────────────────────┐
│ ✓ Upload ─ ✓ Dependency ─ ✓ Understanding ─ ● Generation ─ ○ Verification    │
│                                      ─ ○ Coverage ─ ◌ Runtime Validation      │
└───────────────────────────────────────────────────────────────────────────────┘

Current stage
Test Generation
Generate structured cases from the completed code-understanding run.

Required input
Project             Customer API
Understanding run   fff9…44eb

                                                     [Run Test Generation]
```

Stepper order is always:

`Upload → Dependency → Understanding → Generation → Verification → Coverage → Runtime Validation`

States:

- Completed: blue check, blue connecting line.
- Current: blue dot with 2px ring, dark label.
- Pending: gray circle and line.
- Runtime Validation: disabled dashed circle plus `Coming Soon`.
- Stages are never marked from guessed server state; use active session artifacts.

### 5.5 Dependency Analysis

```text
Dependency Analysis                                      [Run Analysis]
Discover source files, imports, classes, and functions.

Run 0c4f…9861                 Status [Completed]          Project Customer API

[⌕ Search files…] [Language ▾] [Entry points only]
┌───────────────────────────────────────────────────────────────────────────────┐
│ File                  Language    Entry point    Imports   Classes   Functions │
│ app.py                Python      Yes            1         0         2         │
│ utils.py              Python      No             0         0         1         │
└───────────────────────────────────────────────────────────────────────────────┘
```

- Run button: `POST /projects/{id}/dependencies`.
- Result: `GET /dependency-runs/{run_id}`.
- Table fields come only from `FileMetadata`.
- Row expansion shows arrays for imports/classes/functions.
- Empty arrays show `None`, not `0 items found by AI`.

### 5.6 Code Understanding

```text
Code Understanding                                  [Run Understanding]
Inspect architecture, endpoints, rules, flows, and test targets.

Project summary
┌───────────────────────────────────────────────────────────────────────────────┐
│ A small FastAPI application exposing user retrieval and creation endpoints.  │
└───────────────────────────────────────────────────────────────────────────────┘

[Architecture] [Endpoints] [Models] [Business rules] [Flows] [Test targets]

API endpoints
┌───────────────────────────────────────────────────────────────────────────────┐
│ Method  Route              Handler       Request             Response          │
│ GET     /users/{user_id}  get_user      user_id:int         User dictionary   │
└───────────────────────────────────────────────────────────────────────────────┘
```

- Run button calls `/understand` using selected completed dependency `run_id`.
- Summary and architecture use result strings verbatim.
- Tabs map directly to Stage 3 result arrays.
- Endpoint detail drawer may show authentication and side effects only if returned.
- Ambiguities render as neutral warning rows, not errors.

### 5.7 Test Generation

```text
Test Generation                                      [Generate Test Cases]
Generate structured tests from the active understanding run.

┌──────────────────┐ ┌──────────────────┐ ┌──────────────────┐
│ Generated        │ │ After dedupe     │ │ Category coverage│
│ 24               │ │ 21               │ │ 88.9%            │
└──────────────────┘ └──────────────────┘ └──────────────────┘

[⌕ Search tests…] [Category ▾] [Priority ▾] [Severity ▾]
┌───────────────────────────────────────────────────────────────────────────────┐
│ ID       Test case                    Category      Priority      Severity      │
│ TC-001   Create user successfully     Functional    High          Major         │
│ TC-002   Reject missing name          Negative      High          Critical      │
└───────────────────────────────────────────────────────────────────────────────┘
```

- Run calls `/generate-test-cases` with active code-understanding run ID.
- Cards map to `total_generated`, `total_after_deduplication`, and coverage summary.
- Test drawer renders description, preconditions, steps, expected results, requirement IDs, business-rule IDs, and traceability.
- Do not display editable controls; no update-test-case API exists.

### 5.8 Test Verification

```text
Test Verification                                      [Verify Test Cases]
Validate generated tests against analyzed backend code.

┌──────────────────┐ ┌──────────────────┐ ┌──────────────────┐
│ Verified         │ │ Partial          │ │ Failed           │
│ 19               │ │ 3                │ │ 2                │
└──────────────────┘ └──────────────────┘ └──────────────────┘

[⌕ Search IDs…] [Status ▾]
┌───────────────────────────────────────────────────────────────────────────────┐
│ Test ID    Status       Confidence    Findings                  Evidence       │
│ TC-001     Verified     90%           3 checks passed           2 references   │
│ TC-002     Partial      50%           Provider unavailable      2 references   │
└───────────────────────────────────────────────────────────────────────────────┘
```

- Run submits active generated cases to `/verify-test-cases`.
- Status counts map exactly to `summary`.
- `total_verified` must visually equal Verified count.
- Expanded row groups unique findings by `check` and lists file/symbol/line evidence.
- Confidence is text plus a subtle 4px bar; no gauge chart.

### 5.9 Coverage & Quality

```text
Coverage & Quality                                  [Optimize Quality]
Evaluate coverage and improve actionable gaps.

┌──────────────────┐ ┌──────────────────┐ ┌──────────────────┐
│ Final score      │ │ Improvement      │ │ Iterations       │
│ 85 / 100         │ │ +18.33           │ │ 2                │
└──────────────────┘ └──────────────────┘ └──────────────────┘

Quality dimensions
Coverage             100%  ━━━━━━━━━━━━━━━━━━━━
Correctness            50%  ━━━━━━━━━━──────────
Traceability          100%  ━━━━━━━━━━━━━━━━━━━━
Completeness          100%  ━━━━━━━━━━━━━━━━━━━━
Boundary coverage       0%  ────────────────────

Iteration history
┌───────────────────────────────────────────────────────────────────────────────┐
│ Iteration   Score    Verified   Partial   Failed   Result                    │
│ 1           66.67    2          0         0        Regenerated               │
│ 2           85.00    0          6         0        Threshold met             │
└───────────────────────────────────────────────────────────────────────────────┘

Regeneration plan
┌───────────────────────────────────────────────────────────────────────────────┐
│ ADD     Security              Add tests for uncovered categories              │
│ UPDATE  TC-004               Update partially verified test case              │
└───────────────────────────────────────────────────────────────────────────────┘

Stopping reason: Threshold met
```

- `Evaluate Quality` is not a second primary action. It appears in an overflow menu and calls `/evaluate-test-quality`.
- Primary action calls `/optimize-test-quality` using active cases and verification.
- All ten requested dimensions appear as simple horizontal measures.
- History maps to `evaluation_history` and `iteration_summaries`.
- Plans map to `regeneration_plans`; action labels use returned enum values.
- Optimized suite uses `optimized_test_suite` and the same table/drawer as Test Generation.
- Stopping reason displays a humanized returned value without changing meaning.

### 5.10 Export

No server export API exists. This page exports only artifacts already returned to the current browser session; it performs no backend request and promises no server persistence.

```text
Export
Download artifacts available in this browser session.

┌───────────────────────────────────────────────────────────────────────────────┐
│ Artifact                     Available       Format             Action         │
│ Code understanding           Yes             JSON               Download       │
│ Generated test cases         Yes             JSON               Download       │
│ Verification results         Yes             JSON               Download       │
│ Quality optimization         Yes             JSON               Download       │
└───────────────────────────────────────────────────────────────────────────────┘

Artifacts are available only for the active session. Run the corresponding
pipeline stage before downloading.
```

- Download uses `JSON.stringify` on the exact response object and a browser Blob.
- Unavailable rows show disabled action.
- No CSV, PDF, report scheduling, sharing, or server export is shown.

### 5.11 Settings

No backend settings API exists. Keep this page intentionally narrow.

```text
Settings
Configure local interface preferences and inspect API availability.

Appearance
Theme                          Light / System
Density                        Comfortable

API status
Backend                        [Healthy]

Preferences are stored in this browser only.
```

- API status maps to `GET /health`.
- Theme and density are local-storage UI preferences.
- No provider keys, models, retry settings, thresholds, users, teams, or billing controls are exposed.

## 6. Color palette

| Token | Value | Use |
|---|---:|---|
| `canvas` | `#F8FAFC` | application content background |
| `surface` | `#FFFFFF` | cards, sidebar, header, dialogs |
| `surface-subtle` | `#F9FAFB` | table header, quiet hover |
| `border` | `#E5E7EB` | default border |
| `border-strong` | `#D1D5DB` | focused structure |
| `text-primary` | `#111827` | headings and values |
| `text-secondary` | `#4B5563` | body and descriptions |
| `text-muted` | `#6B7280` | captions and metadata |
| `accent` | `#0284C7` | primary actions and active state |
| `accent-hover` | `#0369A1` | primary hover |
| `accent-soft` | `#F0F9FF` | selected background |
| `success` | `#15803D` | completed/verified |
| `success-soft` | `#F0FDF4` | success badge |
| `warning` | `#A16207` | partial/current warning |
| `warning-soft` | `#FEFCE8` | warning badge |
| `danger` | `#B91C1C` | failed/destructive |
| `danger-soft` | `#FEF2F2` | danger badge |

No gradients, transparency effects, glow, or saturated card fills.

## 7. Typography scale

Primary family: `Inter, Geist, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif`.

| Style | Size / line | Weight | Use |
|---|---|---:|---|
| Display | 32 / 40 | 650 | rare empty-state title |
| Page title | 28 / 36 | 650 | page heading |
| Section title | 18 / 28 | 600 | major section |
| Card value | 28 / 36 | 650 | metric value |
| Card title | 13 / 20 | 550 | metric label |
| Body | 14 / 22 | 400 | default content |
| Body strong | 14 / 22 | 550 | emphasized content |
| Small | 13 / 20 | 400 | table metadata |
| Caption | 12 / 18 | 450 | labels and timestamps |
| Mono | 12 / 18 | 450 | IDs, paths, symbols |

- Headings use `-0.02em` tracking.
- UI labels use normal tracking; uppercase is reserved for HTTP methods and tiny status metadata.

## 8. Spacing system

Base unit: 8px.

```text
space-0   0
space-0.5 4px
space-1   8px
space-1.5 12px
space-2   16px
space-3   24px
space-4   32px
space-5   40px
space-6   48px
space-8   64px
```

- Page title to subtitle: 4px.
- Page header to first section: 32px.
- Section to section: 40px.
- Card padding: 20px or 24px.
- Form field gap: 20px.
- Inline control gap: 8px.

## 9. Component design system

### Buttons

| Variant | Height | Treatment |
|---|---:|---|
| Primary | 40px | accent fill, white text, 10px radius |
| Secondary | 40px | white, neutral border, primary text |
| Ghost | 36px | transparent, subtle hover |
| Danger | 40px | white, danger text/border; filled only in confirmation |
| Icon | 36px | square, transparent, neutral border where needed |

- Horizontal padding: 16px; icon gap: 8px.
- Disabled: 45% opacity, no shadow.
- Focus: 2px `#BAE6FD` ring plus 1px accent border.
- Button motion: background/border/color 160ms ease-out.
- Each page has at most one primary button.

### Cards

- White surface, 1px border, 12px radius.
- Shadow: `0 1px 2px rgba(15, 23, 42, 0.04)`.
- No colored top borders or background illustrations.
- Metric card anatomy: 18px Lucide icon, 13px title, 28px value, one 13px description.
- Grid: maximum four metric cards per row.

### Status badges

- Height 24px; radius 999px; 8px horizontal padding.
- 12px/18px medium text; optional 6px status dot.
- Map statuses consistently: completed/verified green, running/current blue, partial amber, failed red, pending gray.

### Forms

- Label 13px medium; input 40px; textarea minimum 96px.
- Border `#D1D5DB`; focus accent; error danger.
- Help/error text 12px/18px.
- Required validation mirrors backend constraints.

### Drawers and dialogs

- Test/evidence detail drawer: 520px, right side, 24px padding.
- Upload dialog: 560px, centered.
- Delete confirmation: 440px.
- Overlay: `rgba(15,23,42,.28)`, no blur.

## 10. Table system

- Container: surface, 1px border, 12px radius, overflow hidden.
- Toolbar: 56px minimum, 16px padding.
- Header: sticky at content-scroll top, 44px, `#F9FAFB`.
- Row: 56px default; 64px when description is present.
- Horizontal cell padding: 16px.
- Header: 12px medium, secondary text.
- Body: 14px, primary text.
- Hover: `#F8FAFC`, 160ms.
- Selected: `#F0F9FF`.
- Pagination: 56px footer; server pagination only for Projects.
- Other tables paginate/filter loaded response data client-side.
- Empty states state the missing prerequisite and link to the implemented preceding stage.
- Mobile tables become labeled stacked rows; never force a 900px horizontal canvas for primary tasks.

## 11. Motion

- Hover/focus: 150–160ms ease-out.
- Drawer/dialog: 200ms cubic-bezier(.2,.8,.2,1).
- Page content: no entrance animation.
- Progress changes: 200ms color transition.
- Respect `prefers-reduced-motion`; disable nonessential transition.

## 12. Responsive behavior

### ≥1280px

- 248px sidebar, full header, four metric cards.
- Content padding 40px.

### 1024–1279px

- 72px icon sidebar with accessible tooltips.
- Header search 320px.
- Metric cards use two columns where needed.
- Stepper can horizontally scroll inside its bordered container.

### 768–1023px

- Sidebar becomes drawer opened from header.
- Header project selector remains; search becomes icon-triggered overlay.
- Content padding 24px.
- Two-column cards.
- Detail layouts stack.

### <768px

- Header: menu, project selector, upload icon button.
- Search opens full-width command sheet.
- Content padding 16px.
- Cards use one column.
- Pipeline stepper becomes vertical while preserving exact stage order.
- Tables become card rows.
- Drawers become full-screen sheets.

## 13. Design tokens

```css
:root {
  --color-canvas: #f8fafc;
  --color-surface: #ffffff;
  --color-surface-subtle: #f9fafb;
  --color-border: #e5e7eb;
  --color-border-strong: #d1d5db;
  --color-text-primary: #111827;
  --color-text-secondary: #4b5563;
  --color-text-muted: #6b7280;
  --color-accent: #0284c7;
  --color-accent-hover: #0369a1;
  --color-accent-soft: #f0f9ff;
  --color-success: #15803d;
  --color-warning: #a16207;
  --color-danger: #b91c1c;

  --font-sans: Inter, Geist, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  --font-mono: "IBM Plex Mono", "SFMono-Regular", Consolas, monospace;

  --space-1: 8px;
  --space-2: 16px;
  --space-3: 24px;
  --space-4: 32px;
  --space-5: 40px;
  --space-6: 48px;

  --radius-control: 10px;
  --radius-card: 12px;
  --shadow-card: 0 1px 2px rgba(15, 23, 42, 0.04);
  --transition-ui: 160ms ease-out;

  --sidebar-width: 248px;
  --sidebar-compact-width: 72px;
  --header-height: 64px;
  --content-max-width: 1440px;
}
```

## 14. React implementation specification

Recommended frontend-only structure:

```text
src/
  app/
    router.tsx
    query-client.ts
    session-artifacts.tsx
  api/
    client.ts
    projects.ts
    dependencies.ts
    pipeline.ts
    schemas.ts
  components/
    app-shell/
    buttons/
    cards/
    data-table/
    dialogs/
    forms/
    pipeline-stepper/
    status-badge/
    test-case-drawer/
  pages/
    overview/
    projects/
    pipeline/
    export/
    settings/
  styles/
    tokens.css
    globals.css
```

- React + TypeScript.
- TanStack Query for server requests/caching.
- TanStack Table for loaded-data tables.
- React Router for routes.
- Lucide React only for icons.
- Generate TypeScript transport types from the existing OpenAPI document; do not hand-invent API fields.
- Use an in-memory/session-storage artifact store keyed by project ID for dependency run ID, understanding run ID, generated cases, verification, and optimization response.
- Never infer a persisted run history that cannot be fetched.
- Error banners render backend `detail` verbatim when safe and pair it with the HTTP status.
- Loading uses restrained skeleton rows matching final geometry.
- Request buttons disable while active and use `Running…`; do not simulate progress percentages.
- Preserve returned enum capitalization in data and humanize only display labels.

## 15. Accessibility and production acceptance

- WCAG 2.2 AA contrast.
- Full keyboard navigation and visible focus.
- Icon-only controls require accessible names and tooltips.
- Tables use semantic table elements on desktop.
- Dialog focus is trapped and restored.
- Status never relies on color alone.
- All timestamps use the browser locale with exact ISO value available in tooltip.
- UUIDs and paths support keyboard copy.
- Destructive project deletion requires explicit confirmation.
- No empty navigation destination except the explicitly disabled Runtime Validation item.
- No fabricated analytics, charts, users, alerts, provider status, costs, schedules, or integrations.
