"""
Framework Detector Service – Module 2 orchestrator.

Iterates over a prioritised list of ``BaseFrameworkDetector`` instances,
returns the first match, or falls back to ``Unknown``.

Features:
- Fast in-memory ZIP inspection for instant deterministic framework detection.
- Zero LLM usage.
- Extensibility: to support a new framework, create a subclass of
  ``BaseFrameworkDetector`` and append it to the ``_detectors`` list.
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from app.services.framework_detection.base_detector import BaseFrameworkDetector
from app.services.framework_detection.angular_detector import AngularDetector
from app.services.framework_detection.nextjs_detector import NextjsDetector
from app.services.framework_detection.react_detector import ReactDetector
from app.utils.input_preprocessor import get_project_workspace
from app.utils.zip_handler import ZipHandler

logger = logging.getLogger(__name__)

# Default ordered detector chain.
# Order matters: more specific frameworks (Next.js) come before generic ones
# (React) so that a Next.js project is not classified as plain React.
_DEFAULT_DETECTORS: List[BaseFrameworkDetector] = [
    AngularDetector(),
    NextjsDetector(),
    ReactDetector(),
]

_UNKNOWN_RESULT: Dict[str, Any] = {
    "framework": "Unknown",
    "confidence": 0,
    "reason": "No supported frontend framework detected.",
}


class FrameworkDetectorService:
    """Orchestrates framework detection by delegating to individual detectors."""

    def __init__(
        self,
        detectors: Optional[List[BaseFrameworkDetector]] = None,
    ) -> None:
        self._detectors = detectors if detectors is not None else _DEFAULT_DETECTORS
        self._zip_handler = ZipHandler()
        logger.info(
            "FrameworkDetectorService initialised with %d detector(s): %s",
            len(self._detectors),
            [d.framework_name for d in self._detectors],
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _load_package_json(project_path: Path) -> Optional[Dict[str, Any]]:
        """Try to read and parse ``package.json`` from *project_path* or top-level subdir.

        Returns ``None`` when the file is missing or unparseable.
        """
        pkg_path = project_path / "package.json"
        if not pkg_path.is_file():
            # Search top-level directory if nested wrapper
            for child in project_path.iterdir():
                if child.is_dir() and (child / "package.json").is_file():
                    pkg_path = child / "package.json"
                    break

        if not pkg_path.is_file():
            logger.debug("package.json not found at %s", project_path)
            return None

        try:
            with pkg_path.open("r", encoding="utf-8") as fh:
                data = json.load(fh)
            logger.debug("package.json loaded from %s", pkg_path)
            return data
        except (json.JSONDecodeError, OSError) as exc:
            logger.warning(
                "Failed to parse package.json at %s: %s", pkg_path, exc
            )
            return None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def detect(self, project_path: str) -> Dict[str, Any]:
        """Run fast deterministic framework detection on the project at *project_path*.

        Args:
            project_path: Absolute path to project source directory or ZIP archive.

        Returns:
            A dict with ``framework``, ``confidence``, and ``reason`` keys.

        Raises:
            FileNotFoundError: If *project_path* does not exist.
            ValueError: If *project_path* is invalid, corrupted, or unsupported.
        """
        path_obj = Path(project_path)
        if not path_obj.exists():
            raise FileNotFoundError(f"Project path does not exist: {project_path}")

        # Fast in-memory ZIP inspection if path points to a ZIP file
        if path_obj.is_file() and path_obj.suffix.lower() == ".zip":
            try:
                insp_res, zf = self._zip_handler.inspect_and_filter_zip(path_obj)
                zf.close()
                if insp_res.detected_framework != "Unknown":
                    logger.info(
                        "Early in-memory ZIP detection: %s (%d%%) - %s in %.2f ms",
                        insp_res.detected_framework,
                        insp_res.confidence,
                        insp_res.detection_reason,
                        insp_res.inspection_time_ms + insp_res.filtering_time_ms,
                    )
                    return {
                        "framework": insp_res.detected_framework,
                        "confidence": insp_res.confidence,
                        "reason": insp_res.detection_reason,
                    }
            except Exception as exc:
                if "corrupted" in str(exc).lower():
                    raise ValueError("ZIP archive is corrupted.") from exc
                logger.warning("Fast ZIP framework inspection skipped: %s", exc)

        with get_project_workspace(project_path) as path:
            logger.info("Starting framework detection for: %s", path)

            package_json = self._load_package_json(path)

            for detector in self._detectors:
                logger.debug("Running detector: %s", detector.framework_name)
                result = detector.detect(path, package_json)
                if result is not None:
                    logger.info(
                        "Framework detected: %s (confidence=%d) – %s",
                        result["framework"],
                        result["confidence"],
                        result["reason"],
                    )
                    return result

            logger.info("No framework detected for: %s", path)
            return dict(_UNKNOWN_RESULT)
