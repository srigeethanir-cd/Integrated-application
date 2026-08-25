"""Prepare uploaded Python project dependencies for isolated runtime validation."""

from __future__ import annotations

import ast
import importlib.util
import logging
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)

_DISTRIBUTION_NAMES = {
    "cv2": "opencv-python",
    "email_validator": "email-validator",
    "jwt": "PyJWT",
    "jose": "python-jose",
    "PIL": "Pillow",
    "sklearn": "scikit-learn",
    "yaml": "PyYAML",
}


@dataclass(frozen=True)
class DependencyPreparationResult:
    success: bool
    dependency_path: Path | None = None
    error: str | None = None
    manifest: Path | None = None


class DependencyPreparer:
    """Install declared dependencies into an isolated target directory."""

    def prepare(
        self, source_root: Path, *, workspace: Path, timeout_seconds: int
    ) -> DependencyPreparationResult:
        manifest = self._manifest(source_root)
        missing_packages = self._missing_import_packages(source_root)
        if manifest is None and not missing_packages:
            return DependencyPreparationResult(success=True)
        dependency_path = workspace / "project-dependencies"
        dependency_path.mkdir(parents=True, exist_ok=True)
        if manifest is None:
            command = [
                sys.executable, "-m", "pip", "install",
                "--disable-pip-version-check", "--target", str(dependency_path),
                *missing_packages,
            ]
        elif manifest.name.casefold() == "requirements.txt":
            command = [
                sys.executable, "-m", "pip", "install",
                "--disable-pip-version-check", "--target", str(dependency_path),
                "-r", str(manifest), *missing_packages,
            ]
        else:
            command = [
                sys.executable, "-m", "pip", "install",
                "--disable-pip-version-check", "--target", str(dependency_path),
                str(manifest.parent), *missing_packages,
            ]
        logger.info(
            "Runtime dependency preparation manifest=%s target=%s",
            manifest or "inferred-imports",
            dependency_path,
        )
        try:
            completed = subprocess.run(
                command,
                cwd=manifest.parent if manifest is not None else source_root,
                capture_output=True,
                text=True,
                timeout=max(timeout_seconds, 1),
                check=False,
            )
        except (OSError, subprocess.TimeoutExpired) as error:
            logger.exception("Runtime dependency preparation failed")
            return DependencyPreparationResult(
                success=False,
                error=f"Dependency preparation failed: {type(error).__name__}",
                manifest=manifest,
            )
        if completed.returncode != 0:
            diagnostic = (completed.stderr or completed.stdout or "pip failed").strip()
            logger.error(
                "Runtime dependency preparation failed manifest=%s exit_code=%d",
                manifest,
                completed.returncode,
            )
            return DependencyPreparationResult(
                success=False,
                error=f"Dependency preparation failed: {diagnostic[-2_000:]}",
                manifest=manifest,
            )
        return DependencyPreparationResult(
            success=True,
            dependency_path=dependency_path,
            manifest=manifest,
        )

    @staticmethod
    def _manifest(source_root: Path) -> Path | None:
        candidates = sorted(
            (
                path for path in source_root.rglob("requirements.txt")
                if ".venv" not in path.parts and "venv" not in path.parts
            ),
            key=lambda path: (len(path.relative_to(source_root).parts), str(path)),
        )
        if candidates:
            return candidates[0]
        pyprojects = sorted(
            (
                path for path in source_root.rglob("pyproject.toml")
                if ".venv" not in path.parts and "venv" not in path.parts
            ),
            key=lambda path: (len(path.relative_to(source_root).parts), str(path)),
        )
        return pyprojects[0] if pyprojects else None

    @staticmethod
    def _missing_import_packages(source_root: Path) -> list[str]:
        local_roots = {
            path.stem for path in source_root.glob("*.py")
        } | {
            path.name for path in source_root.iterdir() if path.is_dir()
        }
        imported: set[str] = set()
        for path in source_root.rglob("*.py"):
            if any(part in {".venv", "venv", "tests"} for part in path.parts):
                continue
            try:
                tree = ast.parse(path.read_text(encoding="utf-8"))
            except (OSError, UnicodeError, SyntaxError):
                continue
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    imported.update(alias.name.split(".", 1)[0] for alias in node.names)
                elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
                    imported.add(node.module.split(".", 1)[0])
        missing = []
        for module in sorted(imported - local_roots - sys.stdlib_module_names):
            try:
                available = importlib.util.find_spec(module) is not None
            except (ImportError, ModuleNotFoundError, ValueError):
                available = False
            if not available:
                missing.append(_DISTRIBUTION_NAMES.get(module, module.replace("_", "-")))
        return missing


__all__ = ["DependencyPreparationResult", "DependencyPreparer"]
