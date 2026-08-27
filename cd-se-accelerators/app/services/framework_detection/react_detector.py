"""
React framework detector.

Detection signals:
- ``react`` in *dependencies* or *devDependencies* in package.json
- ``react-dom`` in *dependencies* or *devDependencies* in package.json
- Presence of ``.jsx`` or ``.tsx`` source files in project workspace
- ``import React`` or ``from 'react'`` in source files
"""

import os
from pathlib import Path
from typing import Any, Dict, Optional

from app.services.framework_detection.base_detector import BaseFrameworkDetector
from app.utils.zip_handler import IGNORED_DIR_NAMES


class ReactDetector(BaseFrameworkDetector):
    """Detects React projects."""

    @property
    def framework_name(self) -> str:
        return "React"

    def detect(
        self, project_path: Path, package_json: Optional[Dict[str, Any]]
    ) -> Optional[Dict[str, Any]]:
        # 1. Package.json dependency analysis
        if package_json is not None:
            all_deps = {
                **package_json.get("dependencies", {}),
                **package_json.get("devDependencies", {}),
            }

            has_react = "react" in all_deps
            has_react_dom = "react-dom" in all_deps
            framework_version = None
            if has_react:
                ver_raw = str(all_deps["react"]).strip("^~>=<")
                framework_version = ver_raw

            if has_react and has_react_dom:
                return {
                    "framework": self.framework_name,
                    "framework_version": framework_version,
                    "confidence": 100,
                    "reason": (
                        "Found 'react' and 'react-dom' in package.json dependencies."
                    ),
                }

            if has_react:
                return {
                    "framework": self.framework_name,
                    "framework_version": framework_version,
                    "confidence": 75,
                    "reason": (
                        "Found 'react' in package.json dependencies "
                        "(react-dom not found)."
                    ),
                }

        # 2. Fast source file search skipping ignored directories
        jsx_tsx_count = 0
        found_import = False
        matching_file = ""

        for root, dirs, files in os.walk(project_path):
            dirs[:] = [d for d in dirs if d not in IGNORED_DIR_NAMES and not d.startswith(".")]
            for f in files:
                f_lower = f.lower()
                if f_lower.endswith(".jsx") or f_lower.endswith(".tsx"):
                    jsx_tsx_count += 1
                elif f_lower.endswith(".js") or f_lower.endswith(".ts"):
                    if not found_import:
                        try:
                            fp = Path(root) / f
                            # Read first 4KB for imports
                            with open(fp, "r", encoding="utf-8", errors="ignore") as fh:
                                content = fh.read(4096)
                                if "import React" in content or "from 'react'" in content or 'from "react"' in content:
                                    found_import = True
                                    matching_file = f
                        except Exception:
                            pass

        if jsx_tsx_count > 0:
            return {
                "framework": self.framework_name,
                "confidence": 90,
                "reason": (
                    f"Found React source files with JSX/TSX extensions ({jsx_tsx_count} files)."
                ),
            }

        if found_import:
            return {
                "framework": self.framework_name,
                "confidence": 85,
                "reason": f"Found React imports in source file ({matching_file}).",
            }

        return None
