# Complete Workspace Lifecycle: End-to-End Workflow

This document describes the complete lifecycle of a single workspace from project initialization through deployment.

---

## Overview

A **workspace** is an isolated project sandbox where:
- UI wireframes are analyzed
- Requirements are decomposed into epics and stories
- Each story generates code in complete isolation
- Shared modules are managed separately
- All artifacts are validated before integration
- Final integration merges everything into a deployable application

**Key Principle:** Never modify `integrated_project/` directly. All work happens in isolated sandboxes first.

---

## Workspace Directory Structure

```
backend/
├── workspace/
│   ├── {project_id}/                      ← Single project workspace root
│   │   ├── epics/                         ← Isolated epic + story sandboxes
│   │   │   ├── EP001/                     ← Epic 1 sandbox
│   │   │   │   ├── US101/                 ← Story 1 isolated workspace
│   │   │   │   │   ├── frontend/          ← Story-specific React components
│   │   │   │   │   ├── backend/           ← Story-specific FastAPI services
│   │   │   │   │   │   ├── database/      ← Story-specific database schemas
│   │   │   │   │   │   └── tests/         ← Story-specific unit tests
│   │   │   │   │   ├── metadata/          ← Story execution metadata
│   │   │   │   │   ├── validation/        ← Validation reports
│   │   │   │   │   ├── traceability/      ← Traceability links
│   │   │   │   │   ├── preview/           ← Preview artifacts
│   │   │   │   │   ├── story.json         ← Story definition
│   │   │   │   │   ├── status.json        ← Approval + validation status
│   │   │   │   │   ├── MergeManifest.json ← Integration instructions for Agent3
│   │   │   │   │   └── StoryExecutionSummary.json
│   │   │   │   ├── US102/                 ← Story 2 isolated workspace
│   │   │   │   └── US103/                 ← Story 3 isolated workspace
│   │   │   ├── EP002/                     ← Epic 2 sandbox
│   │   │   │   ├── US201/
│   │   │   │   └── US202/
│   │   │   └── EP003/                     ← Epic 3 sandbox
│   │   │       └── US301/
│   │   ├── core/                          ← Shared modules (used by multiple stories)
│   │   │   ├── auth/                      ← Authentication logic
│   │   │   ├── middleware/                ← Request/response middleware
│   │   │   ├── utils/                     ← Utility functions
│   │   │   ├── models/                    ← Shared data models
│   │   │   └── hooks/                     ← Shared React hooks
│   │   ├── metadata/                      ← Project-level metadata
│   │   │   ├── blueprint.json             ← Agent1 output: full requirements
│   │   │   ├── dependency_graph.json      ← Story dependencies
│   │   │   ├── component_mapping.json     ← UI component → story mapping
│   │   │   ├── screen_mapping.json        ← Screen → story mapping
│   │   │   ├── story_mapping.json         ← Wireframe → story mapping
│   │   │   ├── missing_ui.json            ← Missing UI components report
│   │   │   ├── generated_ui_requirements.json ← Auto-generated UI specs
│   │   │   ├── frontend_generation_plan.json  ← Frontend generation strategy
│   │   │   └── backend_generation_plan.json   ← Backend generation strategy
│   │   ├── traceability/                  ← Project-level traceability
│   │   │   ├── us101_traceability.json    ← Per-story traceability
│   │   │   ├── us102_traceability.json
│   │   │   └── traceability_matrix.json   ← Full matrix
│   │   ├── validation/                    ← Project-level validation reports
│   │   │   ├── us101_validation.json
│   │   │   └── us102_validation.json
│   │   ├── versions/                      ← Workspace version snapshots
│   │   │   ├── v1.0.0/
│   │   │   └── v1.1.0/
│   │   └── integrated_project/            ← Final merged application
│   │       ├── backend/
│   │       │   └── app/
│   │       │       ├── api/               ← All merged API routes
│   │       │       ├── services/          ← All merged business logic
│   │       │       ├── models/            ← All merged models
│   │       │       └── database/          ← All merged database schemas
│   │       ├── frontend/
│   │       │   └── src/
│   │       │       ├── components/        ← All merged React components
│   │       │       ├── pages/             ← All merged pages
│   │       │       └── hooks/             ← All merged hooks
│   │       ├── docs/                      ← Generated documentation
│   │       ├── MergeReport.json           ← Agent3 merge report
│   │       ├── ValidationReport.json      ← Agent3 validation report
│   │       └── DeploymentManifest.json    ← Deployment instructions
│   └── exports/                           ← Final deployment packages
│       └── {project_id}_v1.0.0.zip
```

---

## Complete Workflow: 10 Stages

### **Stage 1: Project Initialization**

**Trigger:** User uploads wireframe images + requirements document

**Agent:** Agent 0 (Wireframe Analyzer)

**Actions:**
1. Analyze wireframe images using Vision API
2. Extract UI components, screens, navigation flows
3. Detect visual hierarchy, layout patterns, design tokens
4. Generate component tree and screen metadata
5. Map components to screens and navigation graph

**Outputs:**
- `workspace/{project_id}/metadata/wireframe_analysis.json`
- `workspace/{project_id}/metadata/component_tree.json`
- `workspace/{project_id}/metadata/screen_metadata.json`
- `workspace/{project_id}/metadata/navigation_graph.json`
- `workspace/{project_id}/metadata/design_tokens.json`
- `workspace/{project_id}/metadata/layout.json`

**Workspace State:** Empty project workspace created

---

### **Stage 2: Requirements Analysis & Blueprint Generation**

**Agent:** Agent 1 (Blueprint Generator)

**Actions:**
1. Read wireframe analysis from Agent 0
2. Read user requirements document
3. Reconcile wireframe with requirements (detect missing UI)
4. Decompose into Epics and User Stories
5. Generate story-to-component mapping
6. Build dependency graph (story execution order)
7. Create frontend and backend generation plans

**Outputs:**
- `workspace/{project_id}/metadata/blueprint.json` ← **Master requirements document**
- `workspace/{project_id}/metadata/dependency_graph.json`
- `workspace/{project_id}/metadata/story_mapping.json`
- `workspace/{project_id}/metadata/component_mapping.json`
- `workspace/{project_id}/metadata/screen_mapping.json`
- `workspace/{project_id}/metadata/missing_ui.json`
- `workspace/{project_id}/metadata/generated_ui_requirements.json`
- `workspace/{project_id}/metadata/frontend_generation_plan.json`
- `workspace/{project_id}/metadata/backend_generation_plan.json`

**Workspace State:** Blueprint ready, epics/stories defined, no code yet

---

### **Stage 3: Story Workspace Preparation**

**Agent:** Workspace Builder (called by Agent 2)

**Actions:**
1. Create isolated story sandbox: `workspace/{project_id}/epics/{epic_key}/{story_key}/`
2. Create subfolders: `frontend/`, `backend/`, `metadata/`, `validation/`, `traceability/`, `preview/`
3. Write `story.json` (story definition)

**Outputs:**
- `workspace/{project_id}/epics/EP001/US101/` (empty sandbox ready)

**Workspace State:** Isolated story workspace created, ready for code generation

---

### **Stage 4: Story Code Generation (Sandboxed)**

**Agent:** Agent 2 (Story Generator)

**Actions:**
1. **Read reconciliation artifacts (7 files):**
   - `story_mapping.json`
   - `component_mapping.json`
   - `screen_mapping.json`
   - `missing_ui.json`
   - `generated_ui_requirements.json`
   - `frontend_generation_plan.json`
   - `backend_generation_plan.json`

2. **Check if story has missing UI:**
   - If story exists in requirements but NOT in wireframe → use auto-generated UI specs

3. **Analyze existing frontend:**
   - Inspect Agent 0's generated frontend components
   - Extract API expectations (props, endpoints, data shapes)

4. **Check shared modules:**
   - List existing modules in `workspace/{project_id}/core/`
   - Determine if story needs new shared modules (auth, utils, etc.)

5. **Generate story-specific code:**
   - **Frontend:** React TypeScript component (`us101_component.tsx`)
   - **Backend:** FastAPI service (`us101_service.py`)
   - **Database:** SQL schema (`us101_schema.sql`)
   - **API:** FastAPI router (`us101_router.py`)
   - **Tests:** Unit tests (`test_us101.py`)

6. **Write all artifacts to story sandbox:**
   - `workspace/{project_id}/epics/EP001/US101/frontend/us101_component.tsx`
   - `workspace/{project_id}/epics/EP001/US101/backend/us101_service.py`
   - `workspace/{project_id}/epics/EP001/US101/backend/database/us101_schema.sql`
   - `workspace/{project_id}/epics/EP001/US101/backend/us101_router.py`
   - `workspace/{project_id}/epics/EP001/US101/backend/tests/test_us101.py`

**Outputs:**
- All story-specific code files (isolated in story sandbox)
- `story.json` — story definition
- `status.json` — approval status (`approved: false`)
- `preview/preview_summary.json` — preview metadata

**Workspace State:** Story code generated, NOT yet validated

---

### **Stage 5: Story Validation (3-Attempt Auto-Repair)**

**Agent:** Story Validator (called by Agent 2)

**Actions:**
1. **Syntax validation:** Check Python/TypeScript syntax
2. **Import validation:** Verify all imports resolve
3. **API contract validation:** Ensure frontend → backend contract matches
4. **Database schema validation:** Check SQL syntax and foreign keys
5. **Test validation:** Verify tests can run

**Auto-Repair Loop (max 3 attempts):**
- If validation fails → LLM repairs the code → re-validate
- If still fails after 3 attempts → flag for manual review

**Outputs:**
- `workspace/{project_id}/epics/EP001/US101/validation/validation_report.json`
- `workspace/{project_id}/validation/us101_validation.json` (copy)

**Workspace State:** Story code validated (or flagged for manual review)

---

### **Stage 6: Merge Manifest Generation**

**Agent:** Merge Manifest Builder (called by Agent 2)

**Actions:**
1. Analyze all files in story sandbox
2. Determine integration actions for Agent 3:
   - **CREATE:** New files to add to `integrated_project/`
   - **MODIFY:** Existing files to update (e.g., add new route to `main.py`)
   - **MERGE:** Resolve conflicts (e.g., two stories modify same API router)

3. Generate detailed merge instructions with file paths, line numbers, merge strategies

**Outputs:**
- `workspace/{project_id}/epics/EP001/US101/MergeManifest.json`

**Example MergeManifest.json:**
```json
{
  "story_key": "US101",
  "epic_key": "EP001",
  "total_actions": 5,
  "create_count": 4,
  "modify_count": 1,
  "actions": [
    {
      "action": "CREATE",
      "source": "workspace/PROJ-EMP-001/epics/EP001/US101/backend/us101_service.py",
      "target": "workspace/PROJ-EMP-001/integrated_project/backend/app/services/us101_service.py"
    },
    {
      "action": "MODIFY",
      "source": "workspace/PROJ-EMP-001/epics/EP001/US101/backend/us101_router.py",
      "target": "workspace/PROJ-EMP-001/integrated_project/backend/app/api/main.py",
      "merge_strategy": "append_route",
      "merge_point": "line 45"
    }
  ]
}
```

**Workspace State:** Story ready for integration, merge instructions created

---

### **Stage 7: Traceability Recording**

**Agent:** Story Traceability Writer (called by Agent 2)

**Actions:**
1. Link story → generated files
2. Link story → API endpoints
3. Link story → database tables
4. Link story → tests
5. Record lineage (requirements → blueprint → story → code)

**Outputs:**
- `workspace/{project_id}/epics/EP001/US101/traceability/traceability.json`
- `workspace/{project_id}/traceability/us101_traceability.json` (copy)

**Example Traceability:**
```json
{
  "story_key": "US101",
  "epic_key": "EP001",
  "generated_files": [
    "workspace/PROJ-EMP-001/epics/EP001/US101/backend/us101_service.py",
    "workspace/PROJ-EMP-001/epics/EP001/US101/backend/us101_router.py"
  ],
  "api_endpoint": "/api/v1/employees",
  "db_table": "employees",
  "tests": ["workspace/PROJ-EMP-001/epics/EP001/US101/backend/tests/test_us101.py"],
  "requirements": ["REQ-001", "REQ-002"],
  "components": ["EmployeeList", "EmployeeCard"]
}
```

**Workspace State:** Full traceability recorded

---

### **Stage 8: Human Approval Gate**

**Trigger:** User reviews story sandbox via Dashboard UI

**Actions:**
1. User views generated code in Dashboard
2. User reviews validation report
3. User approves or rejects story
4. If rejected → Agent 2 regenerates with feedback
5. If approved → `status.json` updated: `approved: true`

**Outputs:**
- `workspace/{project_id}/epics/EP001/US101/status.json` (updated)

**Workspace State:** Story approved, ready for integration

---

### **Stage 9: Integration & Merge (Agent 3)**

**Agent:** Agent 3 (Merge & Validation Agent)

**Actions:**

**Step 1: Promote Shared Modules**
- Copy `workspace/{project_id}/core/*` → `integrated_project/core/`
- Shared modules (auth, middleware, utils) are promoted first

**Step 2: Merge Approved Stories**
- Read all `MergeManifest.json` files from approved stories
- Execute merge actions in dependency order:
  - **CREATE:** Copy new files
  - **MODIFY:** Insert/append code into existing files
  - **MERGE:** Resolve route/import/schema conflicts

**Step 3: Conflict Resolution**
- Detect route collisions (e.g., two stories register same endpoint)
- Detect schema conflicts (e.g., two stories modify same table)
- Detect import conflicts
- Resolve automatically or flag for manual review

**Step 4: System Validation (3-Attempt Auto-Repair)**
- Run full system validation:
  - All imports resolve
  - All routes are unique
  - All database migrations are valid
  - All tests pass
- If validation fails → LLM repairs → re-validate
- Max 3 attempts

**Outputs:**
- `workspace/{project_id}/integrated_project/` ← **Fully merged application**
- `workspace/{project_id}/integrated_project/MergeReport.json`
- `workspace/{project_id}/integrated_project/ValidationReport.json`
- `workspace/{project_id}/integrated_project/DeploymentManifest.json`

**Workspace State:** Application fully integrated and validated

---

### **Stage 10: Deployment Export**

**Agent:** Artifact Exporter (called by Workspace Builder)

**Actions:**
1. Package `integrated_project/` into deployment bundle
2. Include all dependencies, configs, migrations
3. Generate deployment instructions
4. Create versioned ZIP archive

**Outputs:**
- `backend/exports/{project_id}_v1.0.0.zip`

**Workspace State:** Application ready for deployment

---

## Data Flow Summary

```
┌─────────────────────────────────────────────────────────────────┐
│ INPUT: Wireframe Images + Requirements Document                 │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ AGENT 0: Wireframe Analysis                                      │
│ → Analyze UI components, screens, navigation                    │
│ → Output: wireframe_analysis.json, component_tree.json          │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ AGENT 1: Blueprint Generation                                    │
│ → Reconcile wireframe + requirements                            │
│ → Decompose into Epics & User Stories                           │
│ → Output: blueprint.json, dependency_graph.json, 7 mapping files│
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ WORKSPACE BUILDER: Create Story Sandbox                         │
│ → Create: workspace/{project_id}/epics/{epic}/{story}/          │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ AGENT 2: Story Code Generation (PER STORY)                      │
│ → Read 7 reconciliation artifacts                               │
│ → Generate: frontend, backend, database, API, tests             │
│ → Validate with 3-attempt auto-repair                           │
│ → Output: MergeManifest.json, validation report, traceability   │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ HUMAN APPROVAL GATE                                              │
│ → User reviews generated code in Dashboard UI                   │
│ → Approves or rejects                                           │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ AGENT 3: Integration & Merge                                     │
│ → Promote shared modules                                        │
│ → Merge all approved stories into integrated_project/           │
│ → Resolve conflicts                                             │
│ → Validate with 3-attempt auto-repair                           │
│ → Output: MergeReport.json, ValidationReport.json               │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ ARTIFACT EXPORTER: Deployment Package                           │
│ → Package integrated_project/ into ZIP                          │
│ → Output: exports/{project_id}_v1.0.0.zip                       │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ OUTPUT: Production-Ready Application                             │
└─────────────────────────────────────────────────────────────────┘
```

---

## Key Design Principles

### 1. **Isolation First**
- Every story generates code in its own sandbox
- No direct modification of `integrated_project/` until Agent 3
- Prevents conflicts during parallel story development

### 2. **Reconciliation-Driven**
- Agent 2 ALWAYS reads 7 reconciliation artifacts before generating code
- Handles missing UI components (present in requirements but not in wireframe)
- Ensures wireframe + requirements are perfectly aligned

### 3. **Validation at Every Stage**
- Story validation (Agent 2)
- System validation (Agent 3)
- Both with 3-attempt automated repair loops

### 4. **Full Traceability**
- Every generated file linked back to:
  - Original requirement
  - Blueprint epic/story
  - Wireframe component
  - API endpoint
  - Database table

### 5. **Human-in-the-Loop**
- Approval gate between Agent 2 (generation) and Agent 3 (integration)
- User reviews code before merge
- Dashboard UI for full visibility

---

## Example: Single Story Lifecycle (US101)

**Story:** "As an admin, I want to view all employees in a table"

### Timeline:

| Stage | Agent | Input | Output | Location |
|-------|-------|-------|--------|----------|
| 1 | Agent 0 | Wireframe image | `component_tree.json`, `screen_metadata.json` | `workspace/metadata/` |
| 2 | Agent 1 | Agent 0 output + requirements | `blueprint.json`, `story_mapping.json` | `workspace/metadata/` |
| 3 | Workspace Builder | Story definition | Empty sandbox | `workspace/epics/EP001/US101/` |
| 4 | Agent 2 | 7 reconciliation files | Frontend + Backend code | `workspace/epics/EP001/US101/frontend/`, `backend/` |
| 5 | Story Validator | Generated code | `validation_report.json` | `workspace/epics/EP001/US101/validation/` |
| 6 | Merge Manifest Builder | Story artifacts | `MergeManifest.json` | `workspace/epics/EP001/US101/` |
| 7 | Traceability Writer | Story artifacts | `traceability.json` | `workspace/epics/EP001/US101/traceability/` |
| 8 | Human | Dashboard UI review | `status.json` (approved: true) | `workspace/epics/EP001/US101/` |
| 9 | Agent 3 | `MergeManifest.json` | Merged code in `integrated_project/` | `workspace/integrated_project/` |
| 10 | Artifact Exporter | `integrated_project/` | `PROJ-EMP-001_v1.0.0.zip` | `backend/exports/` |

---

## API Endpoints for Dashboard

The Dashboard UI consumes these endpoints to visualize workspace state:

| Endpoint | Returns | Used By |
|----------|---------|---------|
| `GET /api/v1/projects/` | All projects | Dashboard Hero Banner |
| `GET /api/v1/epics/` | All epics with story counts | Epics Overview |
| `GET /api/v1/stories/` | All stories by epic/status | Metric Cards |
| `GET /api/v1/files/` | Generated files count | Metric Cards |
| `GET /api/v1/approval/status` | Pending approvals | Sidebar, TopBar |
| `GET /api/v1/reports/generation-history` | Agent actions | Recent Activity |
| `GET /api/v1/reports/story-audits` | Story state transitions | Recent Activity |
| `GET /api/v1/project/status` | Pipeline status | Hero Banner |

---

## Conclusion

A single workspace represents the **complete lifecycle** of a software project:

1. **Analyze** wireframes (Agent 0)
2. **Plan** requirements into epics/stories (Agent 1)
3. **Generate** code per story in isolation (Agent 2)
4. **Validate** each story (Story Validator)
5. **Approve** stories (Human)
6. **Integrate** all approved stories (Agent 3)
7. **Validate** integrated application (System Validator)
8. **Export** deployment package (Artifact Exporter)

The workspace structure ensures **isolation**, **traceability**, and **validation** at every step, producing a production-ready application from wireframes and requirements.
