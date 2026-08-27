import os
import ast
import re
from pathlib import Path
from typing import Dict, Any, List

class DependencyVisualizer:
    """Builds import dependency graphs of Python and JS/TS components."""

    def generate_graph(self, root_path: Path) -> Dict[str, Any]:
        """Walk root_path, extract imports, and build dependency nodes and links."""
        nodes = []
        links = []
        file_to_index = {}
        index = 0

        # Scan python files
        py_files = list(root_path.glob("**/*.py"))
        for f in py_files:
            rel_path = str(f.relative_to(root_path))
            file_to_index[rel_path] = index
            nodes.append({"id": index, "label": rel_path, "type": "python"})
            index += 1

        # Scan frontend files
        fe_files = list(root_path.glob("**/*.tsx")) + list(root_path.glob("**/*.jsx")) + list(root_path.glob("**/*.ts"))
        for f in fe_files:
            rel_path = str(f.relative_to(root_path))
            file_to_index[rel_path] = index
            nodes.append({"id": index, "label": rel_path, "type": "frontend"})
            index += 1

        # Find Python imports
        for f in py_files:
            rel_path = str(f.relative_to(root_path))
            src_idx = file_to_index.get(rel_path)
            if src_idx is None:
                continue
            try:
                with open(f, "r", encoding="utf-8", errors="ignore") as file_obj:
                    parsed = ast.parse(file_obj.read())
                for node in ast.walk(parsed):
                    if isinstance(node, ast.Import):
                        for name in node.names:
                            self._match_dep(name.name, src_idx, file_to_index, links)
                    elif isinstance(node, ast.ImportFrom):
                        if node.module:
                            self._match_dep(node.module, src_idx, file_to_index, links)
            except Exception:
                pass

        # Find Frontend imports
        for f in fe_files:
            rel_path = str(f.relative_to(root_path))
            src_idx = file_to_index.get(rel_path)
            if src_idx is None:
                continue
            try:
                with open(f, "r", encoding="utf-8", errors="ignore") as file_obj:
                    content = file_obj.read()
                imports = re.findall(r'import\s+.*?\s+from\s+["\'](.*?)["\']', content)
                for imp in imports:
                    for key, val in file_to_index.items():
                        if imp in key or key.endswith(imp.replace("./", "/")):
                            links.append({"source": src_idx, "target": val, "relation": "imports"})
            except Exception:
                pass

        return {"nodes": nodes, "links": links}

    def _match_dep(self, mod_name: str, src_idx: int, file_to_index: Dict[str, int], links: List[Dict[str, Any]]):
        for key, val in file_to_index.items():
            mod_path_part = mod_name.replace(".", "/")
            if mod_path_part in key:
                links.append({"source": src_idx, "target": val, "relation": "imports"})
                break
