"""
Mapper Registry – Module 4.

Maps framework names (React, Next.js, Angular, etc.) to concrete ``BaseIRMapper``
instances. Eliminates hardcoded if/else statements and provides Open/Closed
extensibility for future framework support.
"""

import logging
from typing import Dict, List
from app.services.ir_generator.base_mapper import BaseIRMapper

logger = logging.getLogger(__name__)


class MapperRegistry:
    """Registry maintaining framework name → BaseIRMapper mappings."""

    def __init__(self) -> None:
        self._mappers: Dict[str, BaseIRMapper] = {}

    def register(self, name: str, mapper: BaseIRMapper) -> None:
        """Register an IR mapper for a framework name.

        Args:
            name: Framework identifier (e.g. "React", "Angular").
            mapper: BaseIRMapper instance.
        """
        if name in self._mappers:
            raise ValueError(f"Mapper already registered for framework: {name}")
        self._mappers[name] = mapper
        logger.info("Registered IR Mapper for framework: %s", name)

    def get_mapper(self, name: str) -> BaseIRMapper:
        """Retrieve registered mapper for a framework name.

        Args:
            name: Framework identifier.

        Returns:
            The associated ``BaseIRMapper`` instance.
        """
        # Alias Next.js to React mapper if needed
        key = "React" if name in ("React", "Next.js") else name
        try:
            return self._mappers[key]
        except KeyError:
            available = ", ".join(self._mappers.keys()) or "(none)"
            raise KeyError(
                f"No IR Mapper registered for framework '{name}'. "
                f"Available mappers: {available}"
            )

    def supported_frameworks(self) -> List[str]:
        """Return a list of all registered framework names."""
        return sorted(self._mappers.keys())
