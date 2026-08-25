"""
Condition Analyzer for FCE.

Extracts conditional rendering, ternary expressions, and logical AND branches.
"""

from typing import Any, Dict, List
from app.services.frontend_context.models import ConditionContextItem


class ConditionAnalyzer:
    """Extracts component rendering conditions and branches."""

    def extract(self, comp_data: Dict[str, Any]) -> List[ConditionContextItem]:
        conditions: List[ConditionContextItem] = []
        raw_conds = comp_data.get("conditional_rendering") or comp_data.get("conditions") or []

        for c in raw_conds:
            if isinstance(c, dict):
                cond_expr = c.get("condition") or c.get("expr") or "isTrue"
                c_type = c.get("type") or "ternary"
                dep_state = c.get("dependent_state") or c.get("state_deps") or []
                ui_elements = c.get("rendered_ui") or c.get("affected_ui") or []

                conditions.append(
                    ConditionContextItem(
                        condition=str(cond_expr),
                        type=str(c_type),
                        dependent_state=[str(s) for s in dep_state],
                        rendered_ui=[str(u) for u in ui_elements],
                    )
                )

        return conditions
