"""
Framework Registry – Central registry mapping framework names to BaseFrameworkStrategy implementations.

Provides OCP-compliant strategy lookup for the common pipeline orchestrator.
"""

import logging
from typing import Dict, List, Optional
from app.services.framework_strategy.base_framework_strategy import BaseFrameworkStrategy
from app.services.framework_strategy.react_strategy import ReactStrategy
from app.services.framework_strategy.angular_strategy import AngularStrategy

logger = logging.getLogger(__name__)


class FrameworkRegistry:
    """Registry maintaining active framework strategies."""

    def __init__(self) -> None:
        self._strategies: Dict[str, BaseFrameworkStrategy] = {}

    def register(self, strategy: BaseFrameworkStrategy) -> None:
        """Register a framework strategy.

        Args:
            strategy: BaseFrameworkStrategy instance.
        """
        key = strategy.framework_name.lower()
        self._strategies[key] = strategy
        logger.info("Registered Framework Strategy: %s", strategy.framework_name)

    def get_strategy(self, framework: str) -> BaseFrameworkStrategy:
        """Retrieve strategy mapped to framework name (case-insensitive).

        Args:
            framework: Framework identifier (e.g. 'React', 'Angular', 'Next.js').

        Returns:
            Registered BaseFrameworkStrategy.

        Raises:
            ValueError: If no strategy is registered for the requested framework.
        """
        key = (framework or "").lower()
        # Next.js maps to React strategy
        if key == "next.js":
            key = "react"

        if key not in self._strategies:
            available = ", ".join(self.supported_frameworks()) or "(none)"
            raise ValueError(
                f"No framework strategy registered for framework '{framework}'. "
                f"Available: {available}"
            )
        return self._strategies[key]

    def supported_frameworks(self) -> List[str]:
        """Return a sorted list of registered framework strategy names."""
        return sorted(s.framework_name for s in self._strategies.values())


def build_default_framework_registry() -> FrameworkRegistry:
    """Construct a registry pre-loaded with ReactStrategy and AngularStrategy."""
    registry = FrameworkRegistry()
    registry.register(ReactStrategy())
    registry.register(AngularStrategy())
    return registry
