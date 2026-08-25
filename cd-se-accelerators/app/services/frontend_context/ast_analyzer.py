"""
AST Analyzer for Frontend Context Extraction Engine (FCE).

Delegates deterministic static parsing to React/Angular AST parsers.
"""

import logging
from typing import Any, Dict, List
from app.services.project_analyzer.react_parser import ReactParser
from app.services.project_analyzer.angular_parser import AngularParser

logger = logging.getLogger(__name__)


class ASTAnalyzer:
    """Delegates parsing to ReactParser or AngularParser deterministically."""

    def __init__(self) -> None:
        self._react_parser = ReactParser()
        self._angular_parser = AngularParser()

    def parse_component_file(self, file_path: str, framework: str = "React") -> List[Dict[str, Any]]:
        """Parse source file using static AST parser."""
        try:
            if framework in ("Angular", "angular"):
                res = self._angular_parser.parse(file_path)
            else:
                res = self._react_parser.parse(file_path)
            
            comps = res.get("components", []) if isinstance(res, dict) else (getattr(res, "components", []) or [])
            comp_dicts = []
            for c in comps:
                if isinstance(c, dict):
                    comp_dicts.append(c)
                elif hasattr(c, "model_dump"):
                    comp_dicts.append(c.model_dump())
            return comp_dicts
        except Exception as exc:
            logger.warning("AST parsing failed for %s (%s): %s", file_path, framework, exc)
            return []
