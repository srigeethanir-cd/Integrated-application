"""Execution manager for executing agent steps with retries, timeouts, and error handling."""

import logging
import time
from typing import Any, Callable, Dict, Optional

logger = logging.getLogger(__name__)


class AgentExecutionManager:
    """Manages resilient agent execution with automatic retries and timing logs."""

    def __init__(self, max_retries: int = 3, retry_delay_seconds: float = 1.0):
        self.max_retries = max_retries
        self.retry_delay_seconds = retry_delay_seconds

    def execute_with_retry(
        self,
        func: Callable[..., Any],
        *args: Any,
        step_name: str = "agent_step",
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """Execute a function with retry logic and duration tracking."""
        start_time = time.perf_counter()
        last_exception: Optional[Exception] = None

        for attempt in range(1, self.max_retries + 1):
            try:
                logger.info("Executing %s (Attempt %d/%d)", step_name, attempt, self.max_retries)
                result = func(*args, **kwargs)
                duration = time.perf_counter() - start_time
                return {
                    "success": True,
                    "result": result,
                    "attempts": attempt,
                    "duration_seconds": round(duration, 3),
                    "error": None,
                }
            except Exception as e:
                last_exception = e
                logger.warning("Attempt %d for %s failed: %s", attempt, step_name, str(e))
                if attempt < self.max_retries:
                    time.sleep(self.retry_delay_seconds)

        duration = time.perf_counter() - start_time
        return {
            "success": False,
            "result": None,
            "attempts": self.max_retries,
            "duration_seconds": round(duration, 3),
            "error": str(last_exception),
        }
