"""Deterministic Stage 2 validation summary from discovered file metadata."""

from __future__ import annotations

import sys
from pathlib import PurePosixPath

GROUPS = {
    "Backend Framework": {"fastapi", "flask", "django", "starlette"},
    "Runtime": {"uvicorn", "gunicorn", "hypercorn"},
    "Database": {"sqlalchemy", "alembic", "psycopg", "psycopg2", "pymongo", "redis"},
    "Authentication": {"jwt", "jose", "python-jose", "passlib", "bcrypt", "oauthlib"},
    "Validation": {"pydantic", "email_validator", "marshmallow"},
    "Testing": {"pytest", "unittest", "hypothesis", "jest", "vitest"},
    "Frontend": {"react", "vue", "angular", "svelte", "next"},
    "HTTP Client": {"axios", "requests", "httpx", "aiohttp", "urllib3"},
}
KNOWN_LOCAL_ROOTS = {"app", "backend", "frontend", "main", "src", "tests", "test"}
CONFIG_SUFFIXES = {".toml", ".yaml", ".yml", ".ini", ".cfg", ".json"}


def _relative_path(value: object) -> str:
    path = str(value).replace("\\", "/")
    parts = list(PurePosixPath(path).parts)
    lowered = [part.lower() for part in parts]
    if "source" in lowered:
        parts = parts[lowered.index("source") + 1 :]
    return PurePosixPath(*parts).as_posix()


def build_dependency_analysis(files) -> dict:
    paths = [_relative_path(item.path) for item in files]
    local = set(KNOWN_LOCAL_ROOTS)
    for path in paths:
        parsed = PurePosixPath(path)
        local.add(parsed.stem.lower())
        local.update(part.lower() for part in parsed.parts[:-1])

    packages: set[str] = set()
    standard_library: set[str] = set()
    for item in files:
        for raw in item.imports or []:
            normalized = str(raw).strip()
            if not normalized or normalized.startswith(('.', '/', '@/', '~/', '#')):
                continue
            package = normalized.split(".", 1)[0].split("/", 1)[0].lower()
            if not package or package in local:
                continue
            if package in sys.stdlib_module_names:
                standard_library.add(package)
            else:
                packages.add(package)

    grouped: dict[str, list[str]] = {name: [] for name in GROUPS}
    grouped["Utilities"] = []
    grouped["Python Standard Library"] = sorted(standard_library)
    for package in sorted(packages):
        group = next(
            (name for name, members in GROUPS.items() if package in members),
            "Utilities",
        )
        grouped[group].append(package)
    grouped = {key: value for key, value in grouped.items() if value}

    languages = sorted({str(item.language).title() for item in files if item.language})
    backend = next(
        (name for key, name in (("fastapi", "FastAPI Backend"), ("django", "Django Backend"), ("flask", "Flask Backend")) if key in packages),
        None,
    )
    frontend = next(
        (name for key, name in (("react", "React Frontend"), ("vue", "Vue Frontend"), ("angular", "Angular Frontend"), ("svelte", "Svelte Frontend")) if key in packages),
        None,
    )
    runtime = "Python" if "Python" in languages else "Node.js" if any(language in {"Javascript", "Typescript"} for language in languages) else None
    lower_paths = " ".join(paths).lower()
    layers = [
        name
        for token, name in (("router", "Router"), ("service", "Service"), ("repository", "Repository"), ("model", "Database"))
        if token in lower_paths
    ]
    if backend and frontend:
        architecture = "Full Stack Web Application"
    elif backend == "FastAPI Backend" and {"Router", "Service"}.issubset(layers):
        architecture = "Layered REST API"
    elif "mvc" in lower_paths or {"Controller", "View", "Model"}.issubset(layers):
        architecture = "MVC"
    elif len(layers) >= 3:
        architecture = "Layered Architecture"
    elif backend and any(token in lower_paths for token in ("microservice", "services/")):
        architecture = "Microservice"
    else:
        architecture = None

    return {
        "primary_language": languages[0] if languages else None,
        "secondary_languages": languages[1:],
        "backend_framework": backend,
        "frontend_framework": frontend,
        "runtime": runtime,
        "repository_type": "Full Stack" if backend and frontend else "Backend" if backend else "Frontend" if frontend else None,
        "architecture_style": architecture,
        "entry_points": sorted(_relative_path(item.path) for item in files if item.is_entry_point),
        "module_count": len(files),
        "source_file_count": len(files),
        "test_file_count": sum("test" in PurePosixPath(path).name.lower() or "tests" in path.lower().split("/") for path in paths),
        "configuration_files": [path for path in paths if PurePosixPath(path).suffix.lower() in CONFIG_SUFFIXES],
        "dependency_count": len(packages),
        "dependencies": sorted(packages),
        "dependency_groups": grouped,
        "modules": sorted(paths),
        "project_structure": layers,
    }
