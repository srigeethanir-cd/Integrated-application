"""
Relationship Analyzer for FCE.

Maps component relationships (Parent -> Child Component -> Hook -> Service/API).
"""

from typing import Any, Dict, List
from app.services.frontend_context.models import ChildComponentContextItem


class RelationshipAnalyzer:
    """Extracts child component usages and prop passings."""

    def extract(self, comp_data: Dict[str, Any]) -> List[ChildComponentContextItem]:
        children: List[ChildComponentContextItem] = []
        raw_children = comp_data.get("children") or comp_data.get("child_components") or comp_data.get("jsx_elements") or []

        for ch in raw_children:
            if isinstance(ch, str):
                if ch and ch[0].isupper() and ch not in [c.name for c in children]:
                    children.append(ChildComponentContextItem(name=ch, props_passed=[]))
            elif isinstance(ch, dict):
                tag = ch.get("name") or ch.get("tag") or "ChildComponent"
                if tag and tag[0].isupper():
                    props = ch.get("attributes") or ch.get("props_passed") or []
                    children.append(
                        ChildComponentContextItem(
                            name=tag,
                            props_passed=[str(p) for p in props],
                        )
                    )

        return children
