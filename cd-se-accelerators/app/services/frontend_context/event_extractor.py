"""
Event Extractor for FCE.

Extracts JSX or template event bindings (onChange, onSubmit, (click)).
"""

from typing import Any, Dict, List
from app.services.frontend_context.models import EventContextItem


class EventExtractor:
    """Extracts component event handlers and JSX/template bindings."""

    def extract(self, comp_data: Dict[str, Any]) -> List[EventContextItem]:
        events: List[EventContextItem] = []
        raw_events = comp_data.get("event_handlers") or comp_data.get("events") or []

        for ev in raw_events:
            if isinstance(ev, dict):
                name = ev.get("name") or ev.get("event") or ev.get("event_type") or "onChange"
                handler = ev.get("handler") or ev.get("function") or ev.get("name") or "handleEvent"
                tag = ev.get("element_tag") or ev.get("element") or "input"
                prev_def = bool(ev.get("prevent_default", False))
                stop_prop = bool(ev.get("stop_propagation", False))

                events.append(
                    EventContextItem(
                        name=name,
                        handler=handler,
                        element_tag=tag,
                        prevent_default=prev_def,
                        stop_propagation=stop_prop,
                    )
                )

        return events
