# AI BA Accelerator — User Stories Code Generator

Production-Ready AI-driven Business Analyst & Engineering Accelerator platform that transforms natural language user stories, tech stack specifications, and wireframes into fully-scaffolded, enterprise-grade software applications.

---

## 🚀 Key Capabilities

- **Agent-1 (Blueprint Engine)**: Analyzes user stories and technical constraints to construct full system architectures (`ProjectManifest.json`, `MasterBlueprint.json`, `ImplementationPlan.json`).
- **Agent-2 (Isolated Story Generator)**: Generates backend code, frontend UI, database migration scripts, API endpoints, and unit tests inside an isolated sandbox (`workspace/<story_id>/`).
- **Validation Engine**: Executes syntax checks, AST analysis, security scans, dependency validation, and API contract matching prior to merging code into the main project.
- **Merge Engine**: Safely merges validated story implementations into the target application repository.
- **Multimodal Visual UI Pipeline**: Transforms UI screenshots/wireframes into clean React components and stylesheets.

---

## 🛠️ Technology Stack

- **Core Runtime**: Python 3.12+
- **Backend Framework**: FastAPI (Async, Pydantic v2, Uvicorn)
- **Database Layer**: PostgreSQL 16 / SQLite via SQLAlchemy 2.0 & Alembic
- **AI / Agent Framework**: LangChain, LangGraph, OpenAI GPT-4o, Google Gemini
- **Frontend Dashboard**: React 18, TypeScript, Vite, Tailwind CSS

---

## 📂 Project Architecture

```
.
├── backend/                 # FastAPI Backend Application
│   ├── agents/               # Multi-Agent Modules (Agent 0, 1, 2, 3)
│   ├── app/                  # FastAPI Core, Routers, Models, Schemas, Services
│   ├── merger/               # Smart AST/Text Merge Engine
│   ├── validators/           # Syntax, Security & Dependency Validators
│   ├── workspace_manager/    # Sandboxed Story Workspace Manager
│   └── main.py               # Backend Application Entry Point
├── frontend/                 # React + TypeScript Dashboard UI
├── configs/                  # Central System Configurations & Logging Specs


│   ├── app_config.yaml       # Application Settings & Agent Controls
│   └── logging.json          # Structured Logging Config
├── docs/                     # System Specifications & API Docs
├── outputs/                  # Scaffolded Production Target Projects
├── workspace/                # Sandboxed Workspaces for In-Progress Stories
├── pyproject.toml            # Python 3.12 Package Specification & Metadata
├── requirements.txt          # Production Dependencies
├── .env.example              # Environment Configuration Template
└── README.md                 # Project Documentation
```

---

## 📍 13-Phase Architecture Roadmap

1. **Phase 1**: Project Foundation (Python 3.12, Metadata, Configs, Logging, Dependencies)
2. **Phase 2**: Database & Configuration (SQLAlchemy Models, Alembic Migrations, Settings)
3. **Phase 3**: Core Framework (Base Repositories, Exceptions, LLM Client Abstractions)
4. **Phase 4**: Agent Framework (Agent 0, Agent 1, Agent 2, Agent 3 Implementations)
5. **Phase 5**: LangGraph Workflow (State Graph Orchestration & State Transitions)
6. **Phase 6**: Workspace Manager (Isolated Story Sandbox & File Writers)
7. **Phase 7**: Traceability (Audit Logs & File Lineage Tracking)
8. **Phase 8**: Validators (Syntax, Security, API Contract & Quality Scans)
9. **Phase 9**: Merge Engine (AST-guided Merge & Conflict Resolution)
10. **Phase 10**: FastAPI Integration (API Routers, Middleware, Open API Specifications)
11. **Phase 11**: Frontend Application (React Dashboard & Component Tree Viewers)
12. **Phase 12**: Testing (Automated Test Suites & End-to-End Pipelines)
13. **Phase 13**: Deployment (Production Packaging & Release Engineering)

---

## ⚡ Quick Start (Local Development)

### 1. Prerequisites
- Python 3.12 or higher
- Node.js 18+ & npm (for Frontend)
- PostgreSQL 16 (Optional, SQLite works out of the box for development)

### 2. Environment Setup
```bash
# Clone repository
git clone <repository-url>
cd final

# Copy environment template
cp .env.example .env

# Create and activate virtual environment
python -m venv .venv
# On Windows:
.venv\Scripts\activate
# On Linux/macOS:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Run Backend API
```bash
cd backend
uvicorn main:app --reload --port 8000
```
Swagger API documentation will be available at `http://localhost:8000/docs`.

### 4. Run Frontend Dashboard
```bash
cd frontend
npm install
npm run dev
```


Dashboard will be available at `http://localhost:5173`.

---

## 📄 License

Internal Enterprise License — All rights reserved.
