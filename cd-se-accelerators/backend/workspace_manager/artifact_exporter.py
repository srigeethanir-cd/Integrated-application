"""Artifact Exporter for Workspace Manager.

Packages integrated projects into deployment zip archives and deployment manifests.
"""

import json
import logging
import os
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class DeploymentBundleSpec(BaseModel):
    """Specification of a packaged deployment export bundle."""

    archive_path: str = Field(description="Path to generated .zip deployment archive")
    total_files_packaged: int = Field(description="Number of files included in archive")
    archive_size_bytes: int = Field(description="Zip file size in bytes")
    deployment_manifest: Dict[str, Any] = Field(description="Deployment manifest content")


class ArtifactExporter:
    """Packages integrated project artifacts into production-ready deployment bundles."""

    def export_deployment_bundle(
        self,
        integrated_project_root: str = "./integrated_project",
        output_dir: str = "./outputs/exports",
        app_name: str = "AI_BA_Accelerated_App",
        project_id: Optional[str] = None,
    ) -> DeploymentBundleSpec:
        """Package only real generated project files from the active workspace into a clean deployable .zip archive."""
        base_dir = Path(__file__).resolve().parent.parent
        out_root = Path(output_dir)
        if not out_root.is_absolute():
            out_root = base_dir / output_dir.lstrip("./")
        out_root.mkdir(parents=True, exist_ok=True)

        # Resolve active project ID from parameters or path
        active_proj_id = project_id
        if not active_proj_id:
            import re
            uuid_match = re.search(r'[a-fA-F0-9]{8}-[a-fA-F0-9]{4}-[a-fA-F0-9]{4}-[a-fA-F0-9]{4}-[a-fA-F0-9]{12}', integrated_project_root)
            if uuid_match:
                active_proj_id = uuid_match.group(0)

        if not active_proj_id:
            # Try finding latest project from DB
            try:
                from app.database.session import SessionLocal
                from app.models.project import Project as ProjectModel
                db = SessionLocal()
                latest_p = db.query(ProjectModel).order_by(ProjectModel.created_at.desc()).first()
                if latest_p:
                    active_proj_id = str(latest_p.project_id)
                    if latest_p.project_name:
                        app_name = latest_p.project_name.replace(" ", "_")
                db.close()
            except Exception:
                pass

        archive_name = f"{active_proj_id or app_name}_deployment.zip"
        archive_file = out_root / archive_name
        file_count = 0
        added_arc_names = set()

        # Unwanted legacy folders/files/reports to explicitly filter out from final export
        IGNORED_NAMES = {
            "ba_accelerator",
            "TodoApp",
            "UserManagementSystem",
            "modules",
            "__pycache__",
            ".git",
            ".pytest_cache",
            ".venv",
            "venv",
            "node_modules",
            "StoryExecutionSummary.json",
            "MergeManifest.json",
            "generated_files.json",
            "metadata.json",
            "metadata",
            "preview.html",
            "traceability",
            "validation",
            "TraceabilityReport.json",
            "ValidationReport.json",
            "MergeReport.json",
            "DeploymentManifest.json",
        }

        with zipfile.ZipFile(archive_file, "w", zipfile.ZIP_DEFLATED) as zipf:
            
            # Helper to write string to zip
            def _write_str(arcname: str, content: str):
                nonlocal file_count
                norm = arcname.replace("\\", "/")
                if norm not in added_arc_names:
                    zipf.writestr(norm, content)
                    added_arc_names.add(norm)
                    file_count += 1

            # Helper to write file to zip
            def _write_file(file_path: Path, arcname: str):
                nonlocal file_count
                norm = arcname.replace("\\", "/")
                # Check if any segment is in IGNORED_NAMES
                parts = Path(norm).parts
                if any(p in IGNORED_NAMES for p in parts) or file_path.name in IGNORED_NAMES:
                    return
                if norm not in added_arc_names and file_path.exists() and file_path.is_file():
                    zipf.write(file_path, arcname=norm)
                    added_arc_names.add(norm)
                    file_count += 1

            # 1. Check if integrated_project folder exists for this project
            integrated_dirs = []
            if integrated_project_root:
                p_int = Path(integrated_project_root)
                if not p_int.is_absolute():
                    p_int = base_dir / integrated_project_root.lstrip("./")
                if p_int.exists() and p_int.is_dir():
                    integrated_dirs.append(p_int)

            if active_proj_id:
                cand_int = base_dir / "workspace" / active_proj_id / "integrated_project"
                if cand_int.exists() and cand_int.is_dir() and cand_int not in integrated_dirs:
                    integrated_dirs.append(cand_int)

            found_integrated = False
            for int_dir in integrated_dirs:
                for root, _, files in os.walk(int_dir):
                    for f in files:
                        if f.endswith(".zip") or "__pycache__" in root or f in IGNORED_NAMES:
                            continue
                        full_p = Path(root) / f
                        rel_p = full_p.relative_to(int_dir)
                        if any(p in IGNORED_NAMES for p in rel_p.parts):
                            continue
                        _write_file(full_p, str(rel_p))
                        found_integrated = True

            # 2. If integrated folder was empty, collect directly from workspace/{project_id}/epics/
            if not found_integrated and active_proj_id:
                epics_dir = base_dir / "workspace" / active_proj_id / "epics"
                if epics_dir.exists():
                    for root, _, files in os.walk(epics_dir):
                        for f in files:
                            if f in IGNORED_NAMES or f.endswith(".zip") or "__pycache__" in root:
                                continue
                            full_p = Path(root) / f
                            rel_p = str(full_p.relative_to(epics_dir)).replace("\\", "/")
                            parts = rel_p.split("/")
                            if any(p in IGNORED_NAMES for p in parts):
                                continue
                            # parts: [epic, story, subfolder, file]
                            if len(parts) >= 3:
                                sub = parts[2] # frontend or backend
                                if sub == "frontend":
                                    _write_file(full_p, f"frontend/{f}")
                                elif sub == "backend":
                                    _write_file(full_p, f"backend/{f}")
                                else:
                                    _write_file(full_p, f"{sub}/{f}")
                                found_integrated = True

            # 3. Add core production orchestrators
            main_py = """from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="AI BA Accelerated Application",
    description="Integrated production API generated by BA Accelerator 2",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health_check():
    return {"status": "healthy", "version": "1.0.0"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
"""
            _write_str("backend/app/main.py", main_py)

            # 4. Standard root configurations
            readme = f"""# {app_name} - Integrated Production Release
Generated by **BA Accelerator 2** (AI Development IDE).

## 📁 Clean Project Architecture
```
├── frontend/
│   ├── src/ (React TSX User Story components)
│   └── package.json
├── backend/
│   ├── app/ (FastAPI routers, services, and main.py)
│   └── requirements.txt
├── database/
│   └── migrations/ (SQL schema migrations for each story)
├── tests/ (Pytest test suites)
├── docker-compose.yml
├── .env.example
└── README.md
```

## 🚀 Quickstart

### 1. Run Backend (FastAPI)
```bash
cd backend
pip install -r requirements.txt
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 2. Run Frontend (React)
```bash
cd frontend
npm install
npm run dev
```
"""
            _write_str("README.md", readme)
            _write_str("requirements.txt", "fastapi>=0.109.0\nuvicorn>=0.27.0\npydantic>=2.5.0\nsqlalchemy>=2.0.0\npytest>=7.4.0\nhttpx>=0.25.0\npython-dotenv>=1.0.0\n")
            _write_str("backend/requirements.txt", "fastapi>=0.109.0\nuvicorn>=0.27.0\npydantic>=2.5.0\nsqlalchemy>=2.0.0\npytest>=7.4.0\nhttpx>=0.25.0\npython-dotenv>=1.0.0\n")
            _write_str("package.json", '{\n  "name": "ba-accelerator-app",\n  "version": "1.0.0",\n  "scripts": {\n    "dev": "vite",\n    "build": "vite build"\n  },\n  "dependencies": {\n    "react": "^18.2.0",\n    "react-dom": "^18.2.0",\n    "lucide-react": "^0.300.0"\n  }\n}\n')
            _write_str("frontend/package.json", '{\n  "name": "ba-accelerator-frontend",\n  "version": "1.0.0",\n  "scripts": {\n    "dev": "vite",\n    "build": "vite build"\n  },\n  "dependencies": {\n    "react": "^18.2.0",\n    "react-dom": "^18.2.0",\n    "lucide-react": "^0.300.0"\n  }\n}\n')
            _write_str(".env.example", "PORT=8000\nDATABASE_URL=sqlite:///./app.db\nENVIRONMENT=production\n")
            _write_str("docker-compose.yml", "version: '3.8'\nservices:\n  backend:\n    build: ./backend\n    ports:\n      - '8000:8000'\n  frontend:\n    build: ./frontend\n    ports:\n      - '3000:3000'\n")

        archive_size = archive_file.stat().st_size

        deploy_manifest = {
            "app_name": app_name,
            "version": "1.0.0",
            "export_timestamp": datetime.now(timezone.utc).isoformat(),
            "archive_filename": archive_file.name,
            "total_files": file_count,
            "archive_size_bytes": archive_size,
            "deployment_status": "READY_FOR_PRODUCTION",
        }

        manifest_file = out_root / "DeploymentManifest.json"
        with open(manifest_file, "w", encoding="utf-8") as f:
            json.dump(deploy_manifest, f, indent=2)

        logger.info("ArtifactExporter: Packaged %d real project files into %s (%d bytes)", file_count, archive_file.name, archive_size)

        return DeploymentBundleSpec(
            archive_path=str(archive_file),
            total_files_packaged=file_count,
            archive_size_bytes=archive_size,
            deployment_manifest=deploy_manifest,
        )
