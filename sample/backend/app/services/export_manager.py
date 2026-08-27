import os
import json
import zipfile
import hashlib
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Any

class ExportManager:
    """Manages packaging, checksum calculation, and archiving of integrated project builds."""

    def __init__(self, exports_root: str = None, generated_root: str = None):
        from app.core.config import get_settings
        settings = get_settings()
        self.exports_root = Path(exports_root) if exports_root else Path(settings.exports_root)
        self.generated_root = Path(generated_root) if generated_root else Path(settings.generated_projects_root)


    def calculate_checksum(self, file_path: Path) -> str:
        """Calculate SHA256 checksum of a file."""
        sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256.update(chunk)
        return sha256.hexdigest()

    def package_project(self, project_id: str, version: str = "1.0") -> Dict[str, Any]:
        """Zip the integrated generated_projects/{project_id} directory into exports/{project_id}/{project_id}_v{version}.zip."""
        from app.core.config import get_settings
        from ui_visualization.approval_service import ApprovalService
        
        settings = get_settings()
        app_service = ApprovalService(workspace_root=settings.workspace_root)
        
        # Enforce project-level approval check
        if not app_service.is_project_approved(project_id):
            raise PermissionError(f"Project {project_id} cannot be exported because project-level governance approval has not been granted.")

        proj_dir = self.generated_root / project_id
        if not proj_dir.exists():
            raise FileNotFoundError(f"Generated project folder not found: {proj_dir}")

        dest_dir = self.exports_root / project_id
        dest_dir.mkdir(parents=True, exist_ok=True)

        zip_filename = f"{project_id}_v{version}.zip"
        zip_path = dest_dir / zip_filename

        # Write files into zip archive
        file_count = 0
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zip_f:
            for root, _, files in os.walk(proj_dir):
                for file in files:
                    if "visualization" in Path(root).parts:
                        continue
                    file_path = Path(root) / file
                    rel_path = os.path.relpath(file_path, proj_dir)
                    zip_f.write(file_path, rel_path)
                    file_count += 1

        # Calculate checksums
        checksum_val = self.calculate_checksum(zip_path)
        checksums = {
            zip_filename: checksum_val
        }

        checksums_file = dest_dir / "checksums.json"
        with open(checksums_file, "w", encoding="utf-8") as f:
            json.dump(checksums, f, indent=2)

        # Write export manifest with Release Notes and Deployment Summary
        manifest = {
            "project_id": project_id,
            "version": version,
            "exported_at": datetime.now(timezone.utc).isoformat(),
            "archive_name": zip_filename,
            "checksums": checksums,
            "status": "RELEASE_READY",
            "version_metadata": {
                "major": 1,
                "minor": 0,
                "build": 1,
                "environment": "production"
            },
            "release_notes": {
                "title": f"Production Release v{version}",
                "description": "Auto-scaffolded production code bundle package from AI BA Accelerator pipeline.",
                "features_included": [
                    "Incremental user story code gen",
                    "Security validation",
                    "AST code integration"
                ]
            },
            "deployment_summary": {
                "total_files_packaged": file_count,
                "archive_size_bytes": zip_path.stat().st_size,
                "target_runtime": "FastAPI Uvicorn / React Static SPA",
                "checksum_verification": "SHA256 compliant"
            }
        }

        manifest_file = dest_dir / "export_manifest.json"
        with open(manifest_file, "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2)

        return {
            "status": "success",
            "zip_path": str(zip_path),
            "checksums_path": str(checksums_file),
            "manifest_path": str(manifest_file),
            "manifest": manifest
        }
