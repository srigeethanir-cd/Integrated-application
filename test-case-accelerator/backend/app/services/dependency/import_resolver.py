# backend/app/services/dependency/import_resolver.py
"""Import Resolver module.

Analyzes a source file, extracts import statements, and resolves them to
absolute file paths within the same project. The concrete logic will be added
later.
"""

from __future__ import annotations

from pathlib import Path
from typing import List, Tuple


class ImportResolver:
    """Resolve imports for a given source file.

    The resolver will return a list of tuples ``(import_name, resolved_path)``
    where ``resolved_path`` may be ``None`` if the import cannot be resolved.
    """

    def __init__(self, project_root: str | Path | None = None) -> None:
        """Initialize with the root of the project to resolve relative imports.

        Args:
            project_root: Absolute path to the project's root directory.
        """
        self.project_root = Path(project_root).resolve() if project_root else None

    def resolve(
        self,
        file_path: str | Path,
        project_root: str | Path | None = None,
    ) -> List[Tuple[str, Path | None]]:
        """Extract and resolve imports from *file_path*.

        Returns a list of ``(import_name, resolved_path)`` tuples.
        """
        import ast

        path = Path(file_path).resolve()
        root = Path(project_root).resolve() if project_root else self.project_root or path.parent
        if path.suffix.lower() != ".py":
            return []
        try:
            tree = ast.parse(path.read_text(encoding="utf-8", errors="replace"))
        except SyntaxError:
            return []

        results: List[Tuple[str, Path | None]] = []
        for node in ast.walk(tree):
            names: list[str] = []
            if isinstance(node, ast.Import):
                names = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom):
                names = [node.module or ""]
            for name in names:
                candidate = root.joinpath(*name.split("."))
                resolved = next(
                    (item for item in (candidate.with_suffix(".py"), candidate / "__init__.py") if item.is_file()),
                    None,
                )
                results.append((name, resolved))
        return results
