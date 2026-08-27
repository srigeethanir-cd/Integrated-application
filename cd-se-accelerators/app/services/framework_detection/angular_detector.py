"""
Angular framework detector.

Detection signals:
- Presence of ``angular.json`` in the project root.
- ``@angular/core`` or ``@angular/*`` in *dependencies* or *devDependencies*.
- Presence of ``.component.ts`` or ``.module.ts`` files.
"""

import os
from pathlib import Path
from typing import Any, Dict, Optional

from app.services.framework_detection.base_detector import BaseFrameworkDetector
from app.utils.zip_handler import IGNORED_DIR_NAMES


class AngularDetector(BaseFrameworkDetector):
    """Detects Angular projects."""

    @property
    def framework_name(self) -> str:
        return "Angular"

    def detect(
        self, project_path: Path, package_json: Optional[Dict[str, Any]]
    ) -> Optional[Dict[str, Any]]:
        has_angular_json = (project_path / "angular.json").is_file()

        has_angular_core = False
        framework_version = None

        if package_json is not None:
            all_deps = {
                **package_json.get("dependencies", {}),
                **package_json.get("devDependencies", {}),
            }
            if "@angular/core" in all_deps:
                has_angular_core = True
                ver_raw = str(all_deps["@angular/core"]).strip("^~>=<")
                framework_version = ver_raw
            elif any(k.startswith("@angular/") for k in all_deps):
                has_angular_core = True
                for k, v in all_deps.items():
                    if k.startswith("@angular/"):
                        framework_version = str(v).strip("^~>=<")
                        break

        # Traversal of complete uploaded project workspace skipping ignored dirs
        ng_files_count = 0
        found_component_decorator = False

        for root, dirs, files in os.walk(project_path):
            dirs[:] = [d for d in dirs if d not in IGNORED_DIR_NAMES and not d.startswith(".")]
            for f in files:
                f_lower = f.lower()
                if (
                    f_lower.endswith(".component.ts")
                    or f_lower.endswith(".module.ts")
                    or f_lower.endswith(".service.ts")
                    or f_lower.endswith(".directive.ts")
                    or f_lower.endswith(".pipe.ts")
                ):
                    ng_files_count += 1

                if f_lower.endswith(".ts") and not found_component_decorator:
                    try:
                        fp = Path(root) / f
                        with open(fp, "r", encoding="utf-8", errors="ignore") as fh:
                            content = fh.read(8192)
                            if "@Component" in content or "@NgModule" in content or "@Injectable" in content:
                                found_component_decorator = True
                    except Exception:
                        pass

        if has_angular_json and has_angular_core:
            return {
                "framework": self.framework_name,
                "framework_version": framework_version,
                "confidence": 100,
                "reason": "Found angular.json and '@angular/core' in package.json dependencies.",
            }

        if has_angular_json:
            return {
                "framework": self.framework_name,
                "framework_version": framework_version,
                "confidence": 90,
                "reason": "Found angular.json in project root.",
            }

        if has_angular_core:
            return {
                "framework": self.framework_name,
                "framework_version": framework_version,
                "confidence": 85,
                "reason": "Found '@angular/*' in package.json dependencies.",
            }

        if found_component_decorator or ng_files_count > 0:
            return {
                "framework": self.framework_name,
                "framework_version": framework_version,
                "confidence": 85,
                "reason": f"Found Angular source files/decorators ({ng_files_count} files).",
            }

        return None

