"""
Function Extractor for FCE.

Extracts functions/methods, parameters, return types, variables read/written, and behaviors.
"""

from typing import Any, Dict, List
from app.services.frontend_context.models import FunctionContextItem


class FunctionExtractor:
    """Extracts component functions and method implementations."""

    def extract(self, comp_data: Dict[str, Any]) -> List[FunctionContextItem]:
        functions: List[FunctionContextItem] = []
        raw_fns = comp_data.get("functions") or []

        for fn in raw_fns:
            if isinstance(fn, dict):
                name = fn.get("name") or "fn"
                params = fn.get("parameters") or fn.get("params") or []
                reads = fn.get("reads") or []
                writes = fn.get("writes") or fn.get("state_modified") or []
                beh = fn.get("behavior") or fn.get("description") or f"executes {name}"
                ret = fn.get("return_type") or fn.get("outputs") or "void"
                is_a = bool(fn.get("is_async", False))

                # Infer reads/writes heuristics if missing
                if not reads and "change" in name.lower():
                    reads = ["event.target.value"]
                if not writes and "email" in name.lower():
                    writes = ["email"]
                elif not writes and "password" in name.lower():
                    writes = ["password"]
                elif not writes and "remember" in name.lower():
                    writes = ["rememberMe"]

                functions.append(
                    FunctionContextItem(
                        name=name,
                        parameters=[str(p) for p in params],
                        reads=[str(r) for r in reads],
                        writes=[str(w) for w in writes],
                        behavior=str(beh),
                        return_type=str(ret),
                        is_async=is_a,
                    )
                )

        return functions
