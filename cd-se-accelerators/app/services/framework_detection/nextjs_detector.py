"""
Next.js framework detector.

Detection signals:
- ``next`` in *dependencies* or *devDependencies*.
- Presence of ``next.config.*`` (js / mjs / ts) in the project root.

Both present → confidence 100.
Only ``next`` dep → confidence 90.
Only config file → confidence 80.

.. note::
   Next.js projects also contain ``react`` and ``react-dom``.  The
   orchestrator gives Next.js detectors higher priority so that a
   Next.js project is not mis-classified as plain React.
"""

from pathlib import Path
from typing import Any, Dict, Optional

from app.services.framework_detection.base_detector import BaseFrameworkDetector


_NEXT_CONFIG_PATTERNS = (
    "next.config.js",
    "next.config.mjs",
    "next.config.ts",
)


class NextjsDetector(BaseFrameworkDetector):
    """Detects Next.js projects."""

    @property
    def framework_name(self) -> str:
        return "Next.js"

    def detect(
        self, project_path: Path, package_json: Optional[Dict[str, Any]]
    ) -> Optional[Dict[str, Any]]:
        has_next_dep = False
        if package_json is not None:
            all_deps = {
                **package_json.get("dependencies", {}),
                **package_json.get("devDependencies", {}),
            }
            has_next_dep = "next" in all_deps

        has_next_config = any(
            (project_path / cfg).is_file() for cfg in _NEXT_CONFIG_PATTERNS
        )

        if has_next_dep and has_next_config:
            return {
                "framework": self.framework_name,
                "confidence": 100,
                "reason": (
                    "Found 'next' in package.json dependencies and "
                    "next.config.* in project root."
                ),
            }

        if has_next_dep:
            return {
                "framework": self.framework_name,
                "confidence": 90,
                "reason": "Found 'next' in package.json dependencies.",
            }

        if has_next_config:
            return {
                "framework": self.framework_name,
                "confidence": 80,
                "reason": "Found next.config.* in project root.",
            }

        return None
