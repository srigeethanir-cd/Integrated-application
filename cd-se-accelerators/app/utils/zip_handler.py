"""
ZIP Handler utility.

Provides secure validation, fast inspection, filtering, and selective extraction
of ZIP archives with:
- Zip Slip protection (directory traversal prevention)
- Archive corruption checks
- Size and file count limits (protection against ZIP bombs)
- Symbolic link rejection
- In-memory package.json & config inspection
- Fast ignore filtering for node_modules, build artifacts, and binaries
- Fine-grained timing measurements
"""

import json
import logging
import os
import time
import zipfile
from dataclasses import dataclass, field
from io import BytesIO
from pathlib import Path
from typing import Any, Dict, Final, List, Optional, Set, Tuple

logger = logging.getLogger(__name__)

# Defaults for resource limits
MAX_ZIP_SIZE_BYTES: Final[int] = 100 * 1024 * 1024  # 100 MB compressed limit
MAX_UNCOMPRESSED_SIZE_BYTES: Final[int] = 500 * 1024 * 1024  # 500 MB uncompressed limit
MAX_FILE_COUNT: Final[int] = 100_000  # Support archives with large node_modules to filter

# Directories to ignore and skip completely before extraction
IGNORED_DIR_NAMES: Final[Set[str]] = {
    "node_modules",
    ".git",
    "dist",
    "build",
    "coverage",
    ".cache",
    ".next",
    ".angular",
    ".vscode",
    ".idea",
    "__pycache__",
    ".turbo",
    ".nuxt",
    "target",
    "runs",
    "uploads",
    "temp",
}

# File extensions to ignore
IGNORED_EXTENSIONS: Final[Set[str]] = {
    ".map",
    ".log",
    ".pyc",
    ".pyo",
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".ico",
    ".svg",
    ".webp",
    ".woff",
    ".woff2",
    ".ttf",
    ".eot",
    ".mp4",
    ".webm",
    ".mp3",
    ".pdf",
    ".zip",
    ".tar",
    ".gz",
    ".7z",
    ".rar",
    ".exe",
    ".dll",
    ".so",
    ".dylib",
}

# Specific filenames to ignore
IGNORED_FILENAMES: Final[Set[str]] = {
    "package-lock.json",
    "yarn.lock",
    "pnpm-lock.yaml",
    "bun.lockb",
    ".DS_Store",
    "thumbs.db",
}

# Relevant file extensions for frontend source code & configuration
RELEVANT_EXTENSIONS: Final[Set[str]] = {
    ".js",
    ".jsx",
    ".ts",
    ".tsx",
    ".html",
    ".css",
    ".scss",
    ".sass",
    ".less",
    ".json",
}


@dataclass
class ZipInspectionResult:
    """Detailed metadata from fast ZIP inspection."""

    total_files: int = 0
    ignored_files: int = 0
    extracted_files: int = 0
    relevant_members: List[zipfile.ZipInfo] = field(default_factory=list)
    package_json: Optional[Dict[str, Any]] = None
    config_files: List[str] = field(default_factory=list)
    has_angular_json: bool = False
    has_vite_config: bool = False
    has_next_config: bool = False
    has_tsconfig: bool = False
    detected_framework: str = "Unknown"
    confidence: int = 0
    detection_reason: str = ""
    inspection_time_ms: float = 0.0
    filtering_time_ms: float = 0.0


def is_ignored_path(rel_path: str) -> bool:
    """Check if a normalized relative path matches ignore rules."""
    norm = rel_path.replace("\\", "/").strip("/")
    parts = norm.split("/")
    
    # Check if any parent directory is in IGNORED_DIR_NAMES or starts with . (hidden system dirs)
    for part in parts[:-1]:
        if part in IGNORED_DIR_NAMES or (part.startswith(".") and part not in {".", ".."}):
            return True

    # If the entry itself is a directory in IGNORED_DIR_NAMES
    if parts[-1] in IGNORED_DIR_NAMES:
        return True

    # Check filename & extension rules
    filename = parts[-1]
    if filename in IGNORED_FILENAMES:
        return True

    dot_pos = filename.rfind(".")
    if dot_pos != -1:
        ext = filename[dot_pos:].lower()
        if ext in IGNORED_EXTENSIONS:
            return True

    return False


class ZipHandler:
    """Handles ZIP archive validation, security checks, fast inspection, and selective extraction."""

    def __init__(
        self,
        max_zip_size: int = MAX_ZIP_SIZE_BYTES,
        max_uncompressed_size: int = MAX_UNCOMPRESSED_SIZE_BYTES,
        max_file_count: int = MAX_FILE_COUNT,
    ) -> None:
        self.max_zip_size = max_zip_size
        self.max_uncompressed_size = max_uncompressed_size
        self.max_file_count = max_file_count

    def _open_zip(self, zip_source: Path | bytes) -> zipfile.ZipFile:
        """Open a ZIP file from Path or bytes."""
        if isinstance(zip_source, (bytes, bytearray)):
            return zipfile.ZipFile(BytesIO(zip_source), "r")
        path = Path(zip_source)
        if not path.exists():
            raise FileNotFoundError(f"Path does not exist: {path}")
        if not path.is_file():
            raise ValueError(f"Path is not a file: {path}")
        if path.suffix.lower() != ".zip":
            raise ValueError(
                f"Unsupported file extension. Expected .zip archive, got: {path.name}"
            )
        if path.stat().st_size > self.max_zip_size:
            raise ValueError(
                f"ZIP archive size ({path.stat().st_size} bytes) exceeds maximum limit "
                f"({self.max_zip_size} bytes)."
            )
        return zipfile.ZipFile(path, "r")

    def validate_zip_file(self, zip_path: Path) -> None:
        """Validate that *zip_path* exists, is a valid non-corrupted ZIP, and complies
        with security bounds.
        """
        if not zip_path.exists():
            raise FileNotFoundError(f"Path does not exist: {zip_path}")
        if not zip_path.is_file():
            raise ValueError(f"Path is not a file: {zip_path}")
        if zip_path.suffix.lower() != ".zip":
            raise ValueError(
                f"Unsupported file extension. Expected .zip archive, got: {zip_path.name}"
            )

        file_size = zip_path.stat().st_size
        if file_size > self.max_zip_size:
            raise ValueError(
                f"ZIP archive size ({file_size} bytes) exceeds maximum limit "
                f"({self.max_zip_size} bytes)."
            )

        if not zipfile.is_zipfile(zip_path):
            raise ValueError("ZIP archive is corrupted.")

        try:
            with zipfile.ZipFile(zip_path, "r") as zf:
                corrupt_file = zf.testzip()
                if corrupt_file is not None:
                    raise ValueError(f"ZIP archive is corrupted. Bad file entry: {corrupt_file}")

                infolist = zf.infolist()
                if len(infolist) > self.max_file_count:
                    raise ValueError(
                        f"ZIP archive contains too many files ({len(infolist)}). "
                        f"Limit is {self.max_file_count}."
                    )

                for info in infolist:
                    name = info.filename
                    if name.startswith("/") or name.startswith("\\"):
                        raise ValueError(f"Unsafe ZIP entry detected: {name}")

                    parts = Path(name).parts
                    if ".." in parts:
                        raise ValueError(
                            f"Unsafe ZIP entry detected (directory traversal attempt): {name}"
                        )

                    # Check for symbolic links (UNIX mode: 0o120000)
                    is_symlink = (info.external_attr >> 16) & 0o120000 == 0o120000
                    if is_symlink:
                        raise ValueError(
                            f"ZIP archive contains unsupported symbolic link: {name}"
                        )

        except zipfile.BadZipFile as exc:
            logger.warning("Corrupted zip detected at %s: %s", zip_path, exc)
            raise ValueError("ZIP archive is corrupted.") from exc
        except (OSError, RuntimeError) as exc:
            if "corrupted" in str(exc).lower() or "bad file" in str(exc).lower():
                raise ValueError("ZIP archive is corrupted.") from exc
            raise

    def inspect_and_filter_zip(
        self, zip_source: Path | bytes
    ) -> Tuple[ZipInspectionResult, zipfile.ZipFile]:
        """Perform fast in-memory inspection of ZIP structure and early framework detection.

        Returns:
            Tuple of (ZipInspectionResult, open ZipFile instance). Caller must close or use context manager.
        """
        insp_start = time.perf_counter()

        try:
            zf = self._open_zip(zip_source)
        except zipfile.BadZipFile as exc:
            raise ValueError("ZIP archive is corrupted.") from exc
        except Exception as exc:
            if "corrupted" in str(exc).lower() or "bad file" in str(exc).lower():
                raise ValueError("ZIP archive is corrupted.") from exc
            raise

        corrupt_file = zf.testzip()
        if corrupt_file is not None:
            zf.close()
            raise ValueError(f"ZIP archive is corrupted. Bad file entry: {corrupt_file}")

        infolist = zf.infolist()
        if len(infolist) > self.max_file_count:
            zf.close()
            raise ValueError(
                f"ZIP archive contains too many files ({len(infolist)}). "
                f"Limit is {self.max_file_count}."
            )

        insp_elapsed_ms = (time.perf_counter() - insp_start) * 1000.0

        filt_start = time.perf_counter()
        total_files = len(infolist)
        ignored_count = 0
        relevant_members: List[zipfile.ZipInfo] = []
        pkg_json_info: Optional[zipfile.ZipInfo] = None
        pkg_json_data: Optional[Dict[str, Any]] = None
        config_files: List[str] = []
        has_angular_json = False
        has_vite_config = False
        has_next_config = False
        has_tsconfig = False

        jsx_tsx_count = 0
        component_ts_count = 0

        for info in infolist:
            name = info.filename
            # Security checks
            if name.startswith("/") or name.startswith("\\"):
                zf.close()
                raise ValueError(f"Unsafe ZIP entry detected: {name}")

            parts = Path(name).parts
            if ".." in parts:
                zf.close()
                raise ValueError(
                    f"Unsafe ZIP entry detected (directory traversal attempt): {name}"
                )

            is_symlink = (info.external_attr >> 16) & 0o120000 == 0o120000
            if is_symlink:
                zf.close()
                raise ValueError(
                    f"ZIP archive contains unsupported symbolic link: {name}"
                )

            # Ignore filter check
            if is_ignored_path(name):
                ignored_count += 1
                continue

            relevant_members.append(info)

            # Check config files & framework indicators
            base_name = os.path.basename(name).lower()
            if base_name == "package.json":
                if pkg_json_info is None or len(name) < len(pkg_json_info.filename):
                    pkg_json_info = info
                config_files.append(name)
            elif base_name == "angular.json":
                has_angular_json = True
                config_files.append(name)
            elif base_name.startswith("vite.config."):
                has_vite_config = True
                config_files.append(name)
            elif base_name.startswith("next.config."):
                has_next_config = True
                config_files.append(name)
            elif base_name == "tsconfig.json":
                has_tsconfig = True
                config_files.append(name)
            
            if base_name.endswith(".jsx") or base_name.endswith(".tsx"):
                jsx_tsx_count += 1
            if ".component." in base_name or ".module." in base_name:
                component_ts_count += 1

        # In-memory parse package.json directly from ZIP
        if pkg_json_info is not None:
            try:
                raw_bytes = zf.read(pkg_json_info)
                pkg_json_data = json.loads(raw_bytes.decode("utf-8", errors="ignore"))
            except Exception as exc:
                logger.warning("Failed to parse in-memory package.json from ZIP: %s", exc)

        # Early deterministic framework detection
        detected_fw = "Unknown"
        confidence = 0
        reason = "No framework signals detected in ZIP archive."

        all_deps: Dict[str, str] = {}
        if pkg_json_data is not None:
            all_deps = {
                **pkg_json_data.get("dependencies", {}),
                **pkg_json_data.get("devDependencies", {}),
            }

        # 1. Angular detection
        if has_angular_json and ("@angular/core" in all_deps or any(k.startswith("@angular/") for k in all_deps)):
            detected_fw = "Angular"
            confidence = 100
            reason = "Found angular.json and '@angular/*' dependencies in package.json."
        elif has_angular_json:
            detected_fw = "Angular"
            confidence = 90
            reason = "Found angular.json in ZIP structure."
        elif "@angular/core" in all_deps or any(k.startswith("@angular/") for k in all_deps):
            detected_fw = "Angular"
            confidence = 90
            reason = "Found '@angular/*' dependencies in package.json."
        # 2. Next.js detection
        elif "next" in all_deps and has_next_config:
            detected_fw = "Next.js"
            confidence = 100
            reason = "Found 'next' in package.json dependencies and next.config.* in ZIP structure."
        elif "next" in all_deps:
            detected_fw = "Next.js"
            confidence = 90
            reason = "Found 'next' in package.json dependencies."
        # 3. React detection
        elif "react" in all_deps and "react-dom" in all_deps:
            detected_fw = "React"
            confidence = 100
            reason = "Found 'react' and 'react-dom' in package.json dependencies."
        elif "react" in all_deps:
            detected_fw = "React"
            confidence = 80
            reason = "Found 'react' in package.json dependencies."
        # 4. Fallbacks based on file extensions/names in ZIP
        elif component_ts_count > 0 and jsx_tsx_count == 0:
            detected_fw = "Angular"
            confidence = 80
            reason = f"Found Angular component/module files ({component_ts_count} files) in ZIP."
        elif jsx_tsx_count > 0:
            detected_fw = "React"
            confidence = 85
            reason = f"Found React JSX/TSX source files ({jsx_tsx_count} files) in ZIP."

        filt_elapsed_ms = (time.perf_counter() - filt_start) * 1000.0

        result = ZipInspectionResult(
            total_files=total_files,
            ignored_files=ignored_count,
            extracted_files=len(relevant_members),
            relevant_members=relevant_members,
            package_json=pkg_json_data,
            config_files=config_files,
            has_angular_json=has_angular_json,
            has_vite_config=has_vite_config,
            has_next_config=has_next_config,
            has_tsconfig=has_tsconfig,
            detected_framework=detected_fw,
            confidence=confidence,
            detection_reason=reason,
            inspection_time_ms=round(insp_elapsed_ms, 2),
            filtering_time_ms=round(filt_elapsed_ms, 2),
        )

        return result, zf

    def extract_selective(
        self,
        zip_source: Path | bytes,
        dest_dir: Path,
        inspection_result: Optional[ZipInspectionResult] = None,
        zf: Optional[zipfile.ZipFile] = None,
    ) -> Tuple[float, ZipInspectionResult]:
        """Selectively extract only relevant non-ignored files into dest_dir.

        Returns:
            Tuple of (extraction_time_ms, ZipInspectionResult)
        """
        dest_dir_resolved = dest_dir.resolve()
        dest_dir_resolved.mkdir(parents=True, exist_ok=True)

        close_zf = False
        if zf is None or inspection_result is None:
            inspection_result, zf = self.inspect_and_filter_zip(zip_source)
            close_zf = True

        ext_start = time.perf_counter()
        try:
            total_uncompressed = 0
            for member in inspection_result.relevant_members:
                total_uncompressed += member.file_size
                if total_uncompressed > self.max_uncompressed_size:
                    raise ValueError("ZIP uncompressed size exceeds maximum allowed limit.")

                target_path = (dest_dir_resolved / member.filename).resolve()

                # Verify target path is strictly within dest_dir (Zip Slip check)
                try:
                    target_path.relative_to(dest_dir_resolved)
                except ValueError:
                    raise ValueError(
                        f"Unsafe ZIP entry detected (directory traversal attempt): {member.filename}"
                    )

                if os.path.commonpath([dest_dir_resolved, target_path]) != str(dest_dir_resolved):
                    raise ValueError(
                        f"Unsafe ZIP entry detected (directory traversal attempt): {member.filename}"
                    )

                if member.is_dir():
                    target_path.mkdir(parents=True, exist_ok=True)
                else:
                    target_path.parent.mkdir(parents=True, exist_ok=True)
                    with zf.open(member, "r") as src, open(target_path, "wb") as dst:
                        while True:
                            chunk = src.read(64 * 1024)
                            if not chunk:
                                break
                            dst.write(chunk)

            ext_elapsed_ms = (time.perf_counter() - ext_start) * 1000.0
            logger.info(
                "Selectively extracted %d files (skipped %d ignored) to %s in %.2f ms",
                len(inspection_result.relevant_members),
                inspection_result.ignored_files,
                dest_dir,
                ext_elapsed_ms,
            )
            return round(ext_elapsed_ms, 2), inspection_result
        finally:
            if close_zf and zf:
                zf.close()

    def extract(self, zip_path: Path, dest_dir: Path) -> float:
        """Safely and selectively extract *zip_path* into *dest_dir*.

        Maintains backward compatibility while applying selective extraction.
        """
        elapsed_ms, _ = self.extract_selective(zip_path, dest_dir)
        return elapsed_ms
