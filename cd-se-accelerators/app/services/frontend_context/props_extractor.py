"""
Props Extractor for FCE.

Extracts props/inputs, types, default values, and required flags from component AST data.
"""

from typing import Any, Dict, List
from app.services.frontend_context.models import PropContextItem


class PropsExtractor:
    """Extracts component props / Angular @Inputs."""

    def extract(self, comp_data: Dict[str, Any]) -> List[PropContextItem]:
        props: List[PropContextItem] = []
        raw_props = comp_data.get("props") or comp_data.get("props_inputs") or []

        for p in raw_props:
            if isinstance(p, str):
                props.append(PropContextItem(name=p, type="any", required=False))
            elif isinstance(p, dict):
                name = p.get("name") or "prop"
                p_type = p.get("type") or p.get("prop_type") or "any"
                default_val = p.get("default_value") or p.get("default")
                req = bool(p.get("required") or p.get("is_required", False))
                props.append(
                    PropContextItem(
                        name=name,
                        type=str(p_type),
                        default_value=str(default_val) if default_val is not None else None,
                        required=req,
                    )
                )

        return props
