"""Extract metadata from discovered source files."""

from __future__ import annotations

import ast
import re
from pathlib import Path

from app.schemas.file_metadata import FileMetadata

from .entrypoint_detector import EntrypointDetector
from .language_detector import LanguageDetector


class MetadataService:
    def __init__(
        self,
        language_detector: LanguageDetector | None = None,
        entrypoint_detector: EntrypointDetector | None = None,
    ) -> None:
        self._language_detector = language_detector or LanguageDetector()
        self._entrypoint_detector = entrypoint_detector or EntrypointDetector()

    def generate(self, files: list[Path]) -> list[FileMetadata]:
        entrypoints = set(self._entrypoint_detector.find_entrypoints(files))
        return [self._extract(path, path in entrypoints) for path in files]

    def _extract(self, path: Path, is_entry_point: bool) -> FileMetadata:
        language = self._language_detector.detect(path)
        text = path.read_text(encoding="utf-8", errors="replace")
        imports: list[str] = []
        classes: list[str] = []
        functions: list[str] = []

        if language == "python":
            try:
                tree = ast.parse(text)
                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        imports.extend(alias.name for alias in node.names)
                    elif isinstance(node, ast.ImportFrom):
                        prefix = "." * node.level + (node.module or "")
                        imports.append(prefix)
                    elif isinstance(node, ast.ClassDef):
                        classes.append(node.name)
                    elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        functions.append(node.name)
            except SyntaxError:
                pass
        else:
            imports = re.findall(
                r"(?:from\s+|require\s*\(\s*|import\s+)[\"']([^\"']+)", text
            )
            classes = re.findall(r"\bclass\s+([A-Za-z_$][\w$]*)", text)
            functions = re.findall(r"\bfunction\s+([A-Za-z_$][\w$]*)", text)

        return FileMetadata(
            path=str(path),
            language=language,
            is_entry_point=is_entry_point,
            imports=imports,
            classes=classes,
            functions=functions,
        )
