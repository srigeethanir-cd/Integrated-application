"""Agent State Manager for tracking workflow context and LangGraph state nodes."""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


class AgentStateManager:
    """Manages global state, execution history, and artifact state across agent steps."""

    def __init__(self, initial_state: Optional[Dict[str, Any]] = None):
        self._state: Dict[str, Any] = initial_state or {
            "current_step": "init",
            "history": [],
            "artifacts": {},
            "errors": [],
            "status": "pending",
        }

    def get_state(self) -> Dict[str, Any]:
        """Return a copy of the current state dict."""
        return dict(self._state)

    def get_value(self, key: str, default: Any = None) -> Any:
        """Get a value from state dict."""
        return self._state.get(key, default)

    def set_value(self, key: str, value: Any) -> None:
        """Update a key in state dict."""
        self._state[key] = value

    def record_step(
        self, agent_name: str, step_name: str, status: str, output: Any = None, error: Optional[str] = None
    ) -> None:
        """Record an execution step into state history."""
        record = {
            "agent_name": agent_name,
            "step_name": step_name,
            "status": status,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "output": output,
            "error": error,
        }
        self._state["history"].append(record)
        self._state["current_step"] = step_name
        self._state["status"] = status
        if error:
            self._state["errors"].append(error)

    def store_artifact(self, artifact_key: str, artifact_data: Any) -> None:
        """Store an artifact object in state."""
        self._state["artifacts"][artifact_key] = artifact_data

    def to_langgraph_dict(self) -> Dict[str, Any]:
        """Export state in a format suitable for LangGraph workflow state dicts."""
        return {
            "agent_state": self.get_state(),
            "last_updated": datetime.now(timezone.utc).isoformat(),
        }
