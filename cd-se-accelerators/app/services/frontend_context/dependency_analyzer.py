"""
Dependency Analyzer for FCE.

Extracts module imports, component dependencies, and external packages.
"""

from typing import Any, Dict, List


class DependencyAnalyzer:
    """Extracts component imports and dependencies."""

    def extract(self, comp_data: Dict[str, Any]) -> List[str]:
        deps: List[str] = []
        raw_deps = comp_data.get("dependencies") or comp_data.get("imports") or []

        for d in raw_deps:
            if isinstance(d, str) and d not in deps:
                deps.append(d)
            elif isinstance(d, dict):
                src = d.get("source") or d.get("name")
                if src and src not in deps:
                    deps.append(str(src))

        return deps
