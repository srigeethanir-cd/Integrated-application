"""
Fast Project Scanner Service – Single-Scan & Project Indexing.

Scans the project directory exactly ONCE, ignoring non-essential directories
(node_modules, .git, dist, build, etc.), computes SHA-256 hashes per file,
and constructs a reusable ProjectIndex.
"""

import hashlib
import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from app.models.scanner_models import ProjectIndex, ScanStats
from app.services.framework_detection.framework_detector_service import FrameworkDetectorService

logger = logging.getLogger(__name__)

# Directory names to completely skip during scan
IGNORED_DIRS: Set[str] = {
    "node_modules",
    ".git",
    "dist",
    "build",
    "coverage",
    ".cache",
    ".angular",
    ".next",
    ".nuxt",
    ".turbo",
    "target",
    "__pycache__",
    ".idea",
    ".vscode",
    "runs",
    "uploads",
    "temp",
}

# File extensions to ignore (binary assets, maps, lock files)
IGNORED_EXTENSIONS: Set[str] = {
    ".map", ".png", ".jpg", ".jpeg", ".gif", ".ico", ".svg", ".webp",
    ".woff", ".woff2", ".ttf", ".eot", ".mp4", ".webm", ".mp3", ".pdf",
    ".zip", ".tar", ".gz", ".7z", ".rar", ".exe", ".dll", ".so", ".dylib",
    ".pyc", ".pyo", ".log"
}

# Specific filenames to ignore
IGNORED_FILENAMES: Set[str] = {
    "package-lock.json",
    "yarn.lock",
    "pnpm-lock.yaml",
    "bun.lockb",
    ".DS_Store",
    "thumbs.db",
}

# File extensions relevant to source code analysis
RELEVANT_EXTENSIONS: Set[str] = {
    ".js", ".jsx", ".ts", ".tsx", ".html", ".css", ".scss", ".less", ".json"
}


class ProjectScannerService:
    """Performs single-pass directory scanning and generates a reusable ProjectIndex."""

    def __init__(self, framework_detector: Optional[FrameworkDetectorService] = None) -> None:
        self._framework_detector = framework_detector or FrameworkDetectorService()

    @staticmethod
    def calculate_file_hash(file_path: Path) -> str:
        """Calculate SHA-256 hash of a file's content."""
        hasher = hashlib.sha256()
        try:
            with open(file_path, "rb") as f:
                while chunk := f.read(65536):
                    hasher.update(chunk)
            return hasher.hexdigest()
        except Exception as exc:
            logger.warning("Failed to calculate hash for %s: %s", file_path, exc)
            return ""

    def scan_project(
        self,
        project_path: str,
        project_id: str,
        pipeline_run_id: str,
    ) -> ProjectIndex:
        """Scan project workspace once and construct ProjectIndex.

        Args:
            project_path: Absolute path to target project workspace directory.
            project_id: Unique project identifier.
            pipeline_run_id: Unique pipeline run identifier.

        Returns:
            ProjectIndex object.
        """
        root_path = Path(project_path).resolve()
        logger.info("ProjectScannerService: Starting single-pass scan of workspace '%s'", root_path)

        total_scanned = 0
        ignored_count = 0
        relevant_files: List[str] = []
        file_hashes: Dict[str, str] = {}
        components: List[Dict[str, Any]] = []
        services: List[Dict[str, Any]] = []
        routes: List[Dict[str, Any]] = []
        hooks: List[Dict[str, Any]] = []
        pages: List[Dict[str, Any]] = []
        utilities: List[Dict[str, Any]] = []
        styles: List[str] = []
        existing_tests: List[str] = []
        configuration_files: List[str] = []
        relevant_deps: Dict[str, str] = {}

        # Source code extensions that may contain components
        _SOURCE_CODE_EXTS: Set[str] = {".js", ".jsx", ".ts", ".tsx"}
        # Style extensions tracked separately
        _STYLE_EXTS: Set[str] = {".css", ".scss", ".less"}

        # 1. Single-pass directory walk
        for dirpath, dirnames, filenames in os.walk(root_path):
            # Prune ignored directories in-place and count them as ignored entries
            skipped_dirs = [d for d in dirnames if d in IGNORED_DIRS or d.startswith(".")]
            ignored_count += len(skipped_dirs)
            dirnames[:] = [d for d in dirnames if d not in IGNORED_DIRS and not d.startswith(".")]

            for filename in filenames:
                total_scanned += 1
                full_file_path = Path(dirpath) / filename

                # Compute relative path in POSIX format
                rel_path = os.path.relpath(full_file_path, root_path).replace("\\", "/")

                # Check ignore rules
                ext = full_file_path.suffix.lower()
                if filename in IGNORED_FILENAMES or ext in IGNORED_EXTENSIONS:
                    ignored_count += 1
                    continue

                if ext not in RELEVANT_EXTENSIONS:
                    ignored_count += 1
                    continue

                # Valid relevant file
                relevant_files.append(rel_path)
                file_hash = self.calculate_file_hash(full_file_path)
                file_hashes[rel_path] = file_hash

                # Categorize file metadata
                rel_lower = rel_path.lower()
                fname_lower = filename.lower()

                # Configuration files (non-exclusive: also tracked as relevant)
                if filename in {"package.json", "angular.json", "tsconfig.json", "vite.config.js", "vite.config.ts"}:
                    configuration_files.append(rel_path)
                    if filename == "package.json":
                        relevant_deps = self._extract_package_dependencies(full_file_path)

                # Style files
                if ext in _STYLE_EXTS:
                    styles.append(rel_path)
                    continue

                # JSON/HTML files that are not config are just tracked as relevant
                if ext in {".json", ".html"}:
                    continue

                # From here, ext is guaranteed to be in _SOURCE_CODE_EXTS

                # --- Classify source code files ---

                # 1. Existing unit test files
                if any(suffix in fname_lower for suffix in [".test.tsx", ".test.ts", ".test.js", ".test.jsx", ".spec.ts", ".spec.js", ".spec.tsx", ".spec.jsx"]):
                    existing_tests.append(rel_path)
                    continue

                # Build common entry dict for source files
                file_entry = {
                    "name": full_file_path.stem,
                    "file_path": rel_path,
                    "file_hash": file_hash,
                    "extension": ext,
                }

                # Strip Angular ".component" suffix for cleaner names
                if file_entry["name"].endswith(".component"):
                    file_entry["name"] = file_entry["name"][:-10]

                # 2. Hook files: use* naming convention or in hooks/ directory
                if fname_lower.startswith("use") or "/hooks/" in rel_lower or "\\hooks\\" in rel_lower:
                    hooks.append(file_entry)
                # 3. Service / API / Provider files
                elif any(kw in fname_lower for kw in ["service", "api", "provider", "client", "adapter", "interceptor"]):
                    services.append(file_entry)
                # 4. Route / Navigation files
                elif any(kw in fname_lower for kw in ["route", "routing", "navigation", "router"]):
                    routes.append(file_entry)
                # 5. Page-level files (in pages/ or views/ directories, or named *Page/*)
                elif "/pages/" in rel_lower or "/views/" in rel_lower or fname_lower.endswith("page.tsx") or fname_lower.endswith("page.jsx") or fname_lower.endswith("page.ts") or fname_lower.endswith("page.js"):
                    pages.append(file_entry)
                # 6. Pure utility / helper / constant / type files
                elif any(kw in fname_lower for kw in ["util", "helper", "constant", "config", "type", "enum", "interface", "mock", "fixture", "setup", "index"]) and ext in {".js", ".ts"}:
                    utilities.append(file_entry)
                else:
                    # 7. Everything else is a potential component
                    # This covers: .jsx, .tsx files always; .js/.ts files with
                    # PascalCase names or in component-like directories
                    components.append(file_entry)

        # 2. Deterministic Framework Detection
        detection = self._framework_detector.detect(str(root_path))
        framework = detection.get("framework", "Unknown")
        confidence = detection.get("confidence", 0)

        # Framework version from package.json if present
        framework_version = self._resolve_framework_version(framework, relevant_deps)

        # 3. Composite project content hash
        hash_list = [f"{p}:{h}" for p, h in sorted(file_hashes.items())]
        composite_hash_str = ";".join(hash_list).encode("utf-8")
        project_hash = hashlib.sha256(composite_hash_str).hexdigest()

        stats = ScanStats(
            total_files_scanned=total_scanned,
            relevant_files=len(relevant_files),
            ignored_files=ignored_count,
            component_files=len(components),
            hook_files=len(hooks),
            page_files=len(pages),
            service_files=len(services),
            utility_files=len(utilities),
        )

        logger.info(
            "ProjectScannerService complete: scanned=%d, relevant=%d, ignored=%d, "
            "components=%d, hooks=%d, pages=%d, services=%d, routes=%d, utilities=%d, "
            "styles=%d, tests=%d, framework=%s (%d%%), project_hash=%s",
            total_scanned,
            len(relevant_files),
            ignored_count,
            len(components),
            len(hooks),
            len(pages),
            len(services),
            len(routes),
            len(utilities),
            len(styles),
            len(existing_tests),
            framework,
            confidence,
            project_hash[:8],
        )

        return ProjectIndex(
            project_root=str(root_path),
            project_id=project_id,
            pipeline_run_id=pipeline_run_id,
            project_hash=project_hash,
            framework=framework,
            framework_version=framework_version,
            source_files=sorted(relevant_files),
            components=components,
            services=services,
            routes=routes,
            hooks=hooks,
            pages=pages,
            utilities=utilities,
            styles=sorted(styles),
            existing_tests=sorted(existing_tests),
            configuration_files=sorted(configuration_files),
            relevant_dependencies=relevant_deps,
            file_hashes=file_hashes,
            stats=stats,
        )

    @staticmethod
    def _extract_package_dependencies(pkg_path: Path) -> Dict[str, str]:
        """Extract frontend dependencies from package.json."""
        try:
            with open(pkg_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            deps = data.get("dependencies", {})
            dev_deps = data.get("devDependencies", {})
            all_deps = {**deps, **dev_deps}
            
            key_pkgs = [
                "react", "react-dom", "@angular/core", "@angular/common",
                "next", "vite", "typescript", "jest", "@testing-library/react"
            ]
            return {k: v for k, v in all_deps.items() if k in key_pkgs}
        except Exception as exc:
            logger.warning("Failed to parse dependencies from %s: %s", pkg_path, exc)
            return {}

    @staticmethod
    def _resolve_framework_version(framework: str, deps: Dict[str, str]) -> Optional[str]:
        """Extract clean version number string from dependencies."""
        raw_version = None
        if framework == "React":
            raw_version = deps.get("react")
        elif framework == "Angular":
            raw_version = deps.get("@angular/core")
        elif framework == "Next.js":
            raw_version = deps.get("next")
            
        if raw_version:
            # Strip npm semver prefixes (^, ~, >=, etc.)
            return raw_version.lstrip("^~>=<v").strip()
        return None
