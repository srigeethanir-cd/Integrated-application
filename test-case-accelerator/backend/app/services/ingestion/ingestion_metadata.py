"""Compute and persist refreshable Stage 1 validation metadata."""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

from app.core.config import settings

METADATA_FILE = "ingestion-metadata.json"
IGNORED_PARTS = {".git", ".venv", "venv", "node_modules", "__pycache__"}
CONFIG_NAMES = {
    "pyproject.toml", "setup.py", "setup.cfg", "package.json",
    "requirements.txt", "dockerfile", "docker-compose.yml",
}
LANGUAGES = {
    ".py": "Python", ".js": "JavaScript", ".jsx": "JavaScript",
    ".ts": "TypeScript", ".tsx": "TypeScript", ".java": "Java",
    ".go": "Go", ".rb": "Ruby", ".php": "PHP", ".rs": "Rust",
}


def collect_ingestion_metadata(
    *,
    project_id,
    project_directory: Path,
    source_directory: Path,
    source_type: str,
    started_at: float,
    archive_name: str | None = None,
    archive_size: int | None = None,
) -> dict[str, Any]:
    files = [path for path in source_directory.rglob("*") if path.is_file()]
    directories = [path for path in source_directory.rglob("*") if path.is_dir()]
    ignored = [path for path in files if IGNORED_PARTS.intersection(path.parts)]
    visible = [path for path in files if path not in ignored]
    config = [
        path for path in visible
        if path.name.lower() in CONFIG_NAMES
        or path.suffix.lower() in {".toml", ".yaml", ".yml", ".ini", ".cfg"}
    ]
    tests = [
        path for path in visible
        if "tests" in {part.lower() for part in path.parts}
        or path.name.lower().startswith("test_")
        or ".test." in path.name.lower()
        or ".spec." in path.name.lower()
    ]
    source_files = [
        path for path in visible
        if path.suffix.lower() in LANGUAGES and path not in tests
    ]
    languages = sorted({LANGUAGES[path.suffix.lower()] for path in visible if path.suffix.lower() in LANGUAGES})
    entrypoints = [
        path.relative_to(source_directory).as_posix()
        for path in visible
        if path.name.lower() in {"main.py", "app.py", "manage.py", "server.py", "index.js", "index.ts", "package.json"}
    ]
    names = {path.name.lower() for path in visible}
    has_backend = bool({"pyproject.toml", "requirements.txt", "manage.py"} & names) or any(path.suffix == ".py" for path in visible)
    has_frontend = "package.json" in names and any(path.suffix.lower() in {".js", ".jsx", ".ts", ".tsx"} for path in visible)
    repository_type = "Full Stack" if has_backend and has_frontend else "Backend" if has_backend else "Frontend" if has_frontend else "General Repository"
    metadata = {
        "processing_time_ms": round((time.perf_counter() - started_at) * 1000),
        "workspace_id": str(project_id),
        "workspace_path": str(project_directory.resolve()),
        "project_root": str(source_directory.resolve()),
        "zip_file_name": archive_name,
        "zip_size": archive_size,
        "extracted_size": sum(path.stat().st_size for path in files),
        "total_files": len(files),
        "total_directories": len(directories),
        "source_file_count": len(source_files),
        "configuration_file_count": len(config),
        "test_file_count": len(tests),
        "ignored_file_count": len(ignored),
        "detected_languages": languages,
        "repository_type": repository_type,
        "entry_point_candidates": sorted(entrypoints),
        "source_type": source_type,
    }
    (project_directory / METADATA_FILE).write_text(
        json.dumps(metadata, indent=2, sort_keys=True), encoding="utf-8"
    )
    return metadata


def load_ingestion_metadata(project_id) -> dict[str, Any] | None:
    path = settings.storage_root.expanduser().resolve() / str(project_id) / METADATA_FILE
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError, TypeError):
        return None
    return payload if isinstance(payload, dict) else None
