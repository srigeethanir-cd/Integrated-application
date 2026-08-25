"""
Hook Extractor for FCE.

Extracts useState, useEffect, useMemo, useCallback, useRef, and custom hooks.
"""

from typing import Any, Dict, List
from app.services.frontend_context.models import HookContextItem


class HookExtractor:
    """Extracts React / custom hook invocations."""

    def extract(self, comp_data: Dict[str, Any]) -> List[HookContextItem]:
        hooks: List[HookContextItem] = []
        raw_hooks = comp_data.get("hooks") or []

        for h in raw_hooks:
            if isinstance(h, str):
                hooks.append(HookContextItem(name=h, dependencies=[], is_custom=not h.startswith("use")))
            elif isinstance(h, dict):
                name = h.get("name") or "useHook"
                deps = h.get("dependencies") or []
                is_cust = bool(h.get("is_custom", not name in ("useState", "useEffect", "useMemo", "useCallback", "useRef", "useContext", "useReducer")))
                params = h.get("params") or []
                ret_vals = h.get("return_values") or []

                hooks.append(
                    HookContextItem(
                        name=name,
                        dependencies=[str(d) for d in deps],
                        is_custom=is_cust,
                        params=[str(p) for p in params],
                        return_values=[str(r) for r in ret_vals],
                    )
                )

        return hooks
