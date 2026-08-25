"""
Behavior Mapper & State Transition Analyzer for FCE.

Converts extracted code facts into explicit behaviors and state transition graphs:
initial state -> trigger -> function/handler -> state update -> resulting state.
"""

from typing import List
from app.services.frontend_context.models import (
    BehaviorMappingItem,
    EventContextItem,
    FunctionContextItem,
    StateContextItem,
    StateTransitionItem,
)


class BehaviorMapper:
    """Maps extracted functions & events to explicit behavior objects and state transitions."""

    def map_behaviors(
        self,
        component_id: str,
        functions: List[FunctionContextItem],
        events: List[EventContextItem],
        states: List[StateContextItem],
    ) -> List[BehaviorMappingItem]:
        behaviors: List[BehaviorMappingItem] = []
        b_count = 1

        for fn in functions:
            fn_name = fn.name
            fn_lower = fn_name.lower()

            # Find matching event trigger
            matching_ev = next((ev for ev in events if ev.handler == fn_name), None)
            trigger_name = matching_ev.name if matching_ev else (f"{fn_name} call")

            # Determine read inputs & state changes
            reads_str = ", ".join(fn.reads) if fn.reads else "parameters"
            writes_str = ", ".join(fn.writes) if fn.writes else "component state"

            effect_desc = f"updates {writes_str}" if fn.writes else fn.behavior or f"executes {fn_name}"

            behaviors.append(
                BehaviorMappingItem(
                    behavior_id=f"BEHAVIOR-{component_id}-{b_count:03d}",
                    component_id=component_id,
                    function=fn_name,
                    trigger=trigger_name,
                    input=reads_str,
                    state_change=writes_str,
                    expected_effect=effect_desc,
                )
            )
            b_count += 1

        return behaviors

    def map_state_transitions(
        self,
        functions: List[FunctionContextItem],
        events: List[EventContextItem],
        states: List[StateContextItem],
    ) -> List[StateTransitionItem]:
        transitions: List[StateTransitionItem] = []

        for st in states:
            init_val = st.initial_value if st.initial_value is not None else "default"
            st_name = st.name
            setter = st.setter or f"set{st_name.capitalize()}"

            # Find function modifying this state variable
            mod_fn = next((fn for fn in functions if st_name in fn.writes or st_name.lower() in fn.name.lower()), None)
            fn_trigger = f"{mod_fn.name}(newValue)" if mod_fn else f"trigger{st_name.capitalize()}Change()"
            setter_call = f'{setter}("user@test.com")' if "email" in st_name.lower() else (f"{setter}(true)" if "boolean" in st.state_type.lower() or "false" in str(init_val).lower() or "true" in str(init_val).lower() else f'{setter}("newValue")')
            res_val = '"user@test.com"' if "email" in st_name.lower() else ("true" if "boolean" in st.state_type.lower() or "false" in str(init_val).lower() or "true" in str(init_val).lower() else '"newValue"')

            transitions.append(
                StateTransitionItem(
                    initial_state=f"{st_name} = {init_val}",
                    triggering_function=fn_trigger,
                    state_transition=setter_call,
                    resulting_state=f"{st_name} = {res_val}",
                )
            )

        return transitions
