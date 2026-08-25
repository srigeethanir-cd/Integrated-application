"""
State Extractor for FCE.

Extracts useState, class state, initial state values, and setters (setEmail, setPassword).
"""

from typing import Any, Dict, List
from app.services.frontend_context.models import StateContextItem


class StateExtractor:
    """Extracts component state variables and setters."""

    def extract(self, comp_data: Dict[str, Any]) -> List[StateContextItem]:
        states: List[StateContextItem] = []
        raw_states = comp_data.get("state") or comp_data.get("states") or []

        for st in raw_states:
            if isinstance(st, dict):
                name = st.get("name") or "stateVar"
                init_val = st.get("initial_value")
                setter = st.get("setter") or st.get("setter_name") or f"set{name.capitalize()}"
                st_type = st.get("state_type") or st.get("type") or "unknown"
                mgmt = st.get("management_type") or "useState"

                states.append(
                    StateContextItem(
                        name=name,
                        initial_value=str(init_val) if init_val is not None else None,
                        setter=setter,
                        state_type=str(st_type),
                        management_type=str(mgmt),
                    )
                )

        return states
