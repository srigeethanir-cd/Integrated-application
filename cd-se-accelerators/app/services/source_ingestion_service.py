"""
Source Ingestion Service – Module 1.

Handles ZIP upload, local project registration, and Git repository cloning.
Each operation creates an isolated workspace under ``uploads/<project_id>/source/``.

Optimizations:
- Early in-memory ZIP inspection and framework detection (0 LLM calls).
- Selective extraction: filters node_modules, build artifacts, .git, caches, and binaries before writing to disk.
- Fast lightweight project indexing during ingestion.
- Granular performance logging and file statistics.
"""

import json
import logging
import os
import shutil
import time
import uuid
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import git

from app.models.scanner_models import ProjectIndex
from app.models.source_models import IngestionPerformanceMetrics, IngestionStats
from app.services.project_scanner.project_scanner_service import ProjectScannerService
from app.utils.file_utils import (
    ensure_directory,
    validate_directory_exists,
    validate_zip_extension,
)
from app.utils.zip_handler import ZipHandler

logger = logging.getLogger(__name__)

# Resolve the uploads root relative to *this* file so it works regardless of
# the working directory the application is started from.
_UPLOADS_ROOT = Path(__file__).resolve().parent.parent / "uploads"


class IngestionResult(tuple):
    """2-tuple (project_id, project_path) enriched with performance metrics and stats."""

    project_id: str
    project_path: str
    detected_framework: str
    stats: IngestionStats
    metrics: IngestionPerformanceMetrics
    project_index: Optional[ProjectIndex]

    def __new__(
        cls,
        project_id: str,
        project_path: str,
        detected_framework: str = "Unknown",
        stats: Optional[IngestionStats] = None,
        metrics: Optional[IngestionPerformanceMetrics] = None,
        project_index: Optional[ProjectIndex] = None,
    ) -> "IngestionResult":
        obj = super().__new__(cls, (project_id, project_path))
        obj.project_id = project_id
        obj.project_path = project_path
        obj.detected_framework = detected_framework
        obj.stats = stats or IngestionStats()
        obj.metrics = metrics or IngestionPerformanceMetrics()
        obj.project_index = project_index
        return obj


class SourceIngestionService:
    """Encapsulates all source-ingestion workflows.

    Every public method returns a ``(project_id, project_path)`` tuple / ``IngestionResult`` on
    success and raises on invalid input or I/O errors.
    """

    def __init__(self, uploads_root: Path | None = None) -> None:
        self._uploads_root = uploads_root or _UPLOADS_ROOT
        ensure_directory(self._uploads_root)
        self._zip_handler = ZipHandler()
        self._scanner_service = ProjectScannerService()
        logger.info("SourceIngestionService initialised – uploads root: %s", self._uploads_root)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _generate_project_id(self) -> str:
        """Return a unique, filesystem-safe project identifier."""
        return uuid.uuid4().hex

    def _project_source_dir(self, project_id: str, allow_existing: bool = False) -> Path:
        """Return ``uploads/<project_id>/source/`` and ensure it does *not*
        already exist (prevents accidental overwrites unless allow_existing is True)."""
        project_dir = self._uploads_root / project_id / "source"
        if not allow_existing and project_dir.exists():
            raise FileExistsError(
                f"Project workspace already exists: {project_dir}"
            )
        return ensure_directory(project_dir)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def upload_zip(
        self, filename: str, file_bytes: bytes
    ) -> IngestionResult:
        """Accept raw ZIP bytes, validate, early detect framework, selectively extract, and index.

        Args:
            filename: Original filename of the uploaded file.
            file_bytes: Raw bytes of the uploaded ZIP archive.

        Returns:
            An ``IngestionResult`` tuple containing ``(project_id, project_path)`` and metadata.

        Raises:
            ValueError: If the file extension is not ``.zip`` or the archive is corrupted.
        """
        total_start = time.perf_counter()
        validate_zip_extension(filename)
        upload_start = time.perf_counter()

        logger.info("Received ZIP upload: %s (%d bytes)", filename, len(file_bytes))
        upload_time_ms = (time.perf_counter() - upload_start) * 1000.0

        project_id = self._generate_project_id()
        source_dir = self._project_source_dir(project_id)

        try:
            # 1. Fast in-memory ZIP inspection and early framework detection
            fw_detect_start = time.perf_counter()
            inspection_res, zf = self._zip_handler.inspect_and_filter_zip(file_bytes)
            fw_detect_time_ms = (time.perf_counter() - fw_detect_start) * 1000.0

            logger.info(
                "Early Framework Detection: %s (%d%% confidence) - %s (took %.2f ms)",
                inspection_res.detected_framework,
                inspection_res.confidence,
                inspection_res.detection_reason,
                fw_detect_time_ms,
            )

            # 2. Selective Extraction: only extract relevant non-ignored files
            ext_elapsed_ms, _ = self._zip_handler.extract_selective(
                file_bytes, source_dir, inspection_result=inspection_res, zf=zf
            )
            zf.close()

            # Save project_meta.json with original uploaded filename and hash
            try:
                from app.services.cache_service import compute_project_content_hash, redis_pipeline_cache
                zip_hash = compute_project_content_hash(file_bytes)
                redis_pipeline_cache.link_project_to_hash(project_id, zip_hash)
                with open(source_dir / "project_meta.json", "w", encoding="utf-8") as f:
                    json.dump({"original_filename": filename, "zip_hash": zip_hash}, f, indent=2)
            except Exception as exc:
                logger.warning("Could not write project_meta.json: %s", exc)

            # 3. Project Index Creation
            idx_start = time.perf_counter()
            project_index = self._scanner_service.scan_project(
                str(source_dir), project_id=project_id, pipeline_run_id=f"run_{project_id[:8]}"
            )
            if inspection_res.detected_framework != "Unknown":
                project_index.framework = inspection_res.detected_framework
            idx_elapsed_ms = (time.perf_counter() - idx_start) * 1000.0

            total_elapsed_ms = (time.perf_counter() - total_start) * 1000.0

            stats = IngestionStats(
                total_files=inspection_res.total_files,
                ignored_files=inspection_res.ignored_files,
                extracted_files=inspection_res.extracted_files,
                processed_files=len(project_index.source_files),
            )

            metrics = IngestionPerformanceMetrics(
                upload_time_ms=round(upload_time_ms, 2),
                zip_inspection_time_ms=inspection_res.inspection_time_ms,
                file_filtering_time_ms=inspection_res.filtering_time_ms,
                framework_detection_time_ms=round(fw_detect_time_ms, 2),
                extraction_time_ms=round(ext_elapsed_ms, 2),
                project_index_time_ms=round(idx_elapsed_ms, 2),
                total_ingestion_time_ms=round(total_elapsed_ms, 2),
            )

            # Save project_index.json inside workspace for durability
            idx_file = source_dir / "project_index.json"
            try:
                with open(idx_file, "w", encoding="utf-8") as f:
                    json.dump(project_index.model_dump(), f, indent=2)
            except Exception as exc:
                logger.warning("Could not persist initial project_index.json: %s", exc)

            logger.info(
                "Source Ingestion Complete: project_id=%s, path=%s, framework=%s, "
                "total_files=%d, ignored=%d, extracted=%d, total_time=%.2f ms",
                project_id,
                source_dir,
                inspection_res.detected_framework,
                stats.total_files,
                stats.ignored_files,
                stats.extracted_files,
                total_elapsed_ms,
            )

            return IngestionResult(
                project_id=project_id,
                project_path=str(source_dir),
                detected_framework=inspection_res.detected_framework,
                stats=stats,
                metrics=metrics,
                project_index=project_index,
            )

        except Exception:
            shutil.rmtree(source_dir.parent, ignore_errors=True)
            raise

    async def register_local_project(
        self, project_path: str, project_id: Optional[str] = None
    ) -> IngestionResult:
        """Register an existing local directory as a project workspace.

        The directory's contents are **copied** into a new workspace skipping ignored folders.
        """
        total_start = time.perf_counter()
        src = Path(project_path).resolve()
        validate_directory_exists(src)
        logger.info("Registering local project: %s", src)

        project_id = project_id or self._generate_project_id()
        source_dir = self._project_source_dir(project_id, allow_existing=True).resolve()

        if src == source_dir:
            logger.info("Project path is already the source directory for project_id=%s, skipping self-copy", project_id)
            idx_file = source_dir / "project_index.json"
            project_index = None
            if idx_file.exists():
                try:
                    with open(idx_file, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    project_index = ProjectIndex.model_validate(data)
                except Exception:
                    pass
            if not project_index:
                try:
                    project_index = self._scanner_service.scan_project(
                        str(source_dir), project_id=project_id, pipeline_run_id=f"run_{project_id[:8]}"
                    )
                except Exception:
                    pass

            return IngestionResult(
                project_id=project_id,
                project_path=str(source_dir),
                detected_framework=getattr(project_index, "framework", "Unknown") if project_index else "Unknown",
                stats=IngestionStats(),
                metrics=IngestionPerformanceMetrics(),
                project_index=project_index,
            )

        if source_dir.exists():
            shutil.rmtree(source_dir, ignore_errors=True)
            ensure_directory(source_dir)

        _IGNORED_DIRS = shutil.ignore_patterns(
            "node_modules",
            ".git",
            "dist",
            "build",
            "coverage",
            ".next",
            ".nuxt",
            ".cache",
            ".turbo",
            ".angular",
            ".vscode",
            ".idea",
            "__pycache__",
            "*.pyc",
            "*.map",
            "*.log",
        )

        try:
            copy_start = time.perf_counter()
            shutil.copytree(src, source_dir, dirs_exist_ok=True, ignore=_IGNORED_DIRS)
            copy_time_ms = (time.perf_counter() - copy_start) * 1000.0
            total_time_ms = (time.perf_counter() - total_start) * 1000.0

            # Generate lightweight index on freshly registered directory
            idx_file = source_dir / "project_index.json"
            project_index = None
            try:
                project_index = self._scanner_service.scan_project(
                    str(source_dir), project_id=project_id, pipeline_run_id=f"run_{project_id[:8]}"
                )
                with open(idx_file, "w", encoding="utf-8") as f:
                    json.dump(project_index.model_dump(), f, indent=2)
            except Exception as exc:
                logger.warning("Could not persist initial project_index.json during local registration: %s", exc)

            metrics = IngestionPerformanceMetrics(
                upload_time_ms=0.0,
                zip_inspection_time_ms=0.0,
                file_filtering_time_ms=0.0,
                framework_detection_time_ms=0.0,
                extraction_time_ms=round(copy_time_ms, 2),
                project_index_time_ms=0.0,
                total_ingestion_time_ms=round(total_time_ms, 2),
            )

            return IngestionResult(
                project_id=project_id,
                project_path=str(source_dir),
                detected_framework=getattr(project_index, "framework", "Unknown") if project_index else "Unknown",
                stats=IngestionStats(),
                metrics=metrics,
                project_index=project_index,
            )
        except Exception:
            shutil.rmtree(source_dir.parent, ignore_errors=True)
            raise

    async def clone_repository(self, repo_url: str) -> IngestionResult:
        """Clone a remote Git repository into a new workspace."""
        total_start = time.perf_counter()
        logger.info("Cloning Git repository: %s", repo_url)

        project_id = self._generate_project_id()
        source_dir = self._project_source_dir(project_id)

        try:
            clone_start = time.perf_counter()
            git.Repo.clone_from(repo_url, str(source_dir))
            clone_time_ms = (time.perf_counter() - clone_start) * 1000.0
            total_time_ms = (time.perf_counter() - total_start) * 1000.0

            metrics = IngestionPerformanceMetrics(
                upload_time_ms=0.0,
                zip_inspection_time_ms=0.0,
                file_filtering_time_ms=0.0,
                framework_detection_time_ms=0.0,
                extraction_time_ms=round(clone_time_ms, 2),
                project_index_time_ms=0.0,
                total_ingestion_time_ms=round(total_time_ms, 2),
            )

            return IngestionResult(
                project_id=project_id,
                project_path=str(source_dir),
                detected_framework="Unknown",
                stats=IngestionStats(),
                metrics=metrics,
                project_index=None,
            )
        except Exception:
            shutil.rmtree(source_dir.parent, ignore_errors=True)
            raise
