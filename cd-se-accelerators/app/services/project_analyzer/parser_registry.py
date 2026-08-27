"""
Parser Registry – maps framework names to ``BaseParser`` instances.

Eliminates hardcoded if/else chains.  Adding a new framework is a single
``register()`` call — no existing code needs to change (OCP).

Usage::

    registry = ParserRegistry()
    registry.register("React", ReactParser())
    registry.register("Angular", AngularParser())

    parser = registry.get_parser("React")  # returns ReactParser instance
"""

import logging
from typing import Dict, List

from app.services.project_analyzer.base_parser import BaseParser

logger = logging.getLogger(__name__)


class ParserRegistry:
    """Central lookup that maps framework names to parser instances."""

    def __init__(self) -> None:
        self._parsers: Dict[str, BaseParser] = {}

    def register(self, name: str, parser: BaseParser) -> None:
        """Register a parser for *name*.

        Args:
            name: Framework name (e.g. ``"React"``, ``"Angular"``).
            parser: A ``BaseParser`` instance that handles this framework.

        Raises:
            ValueError: If *name* is already registered.
        """
        if name in self._parsers:
            raise ValueError(
                f"Parser already registered for framework: {name}"
            )
        self._parsers[name] = parser
        logger.info("Registered parser for framework: %s", name)

    def get_parser(self, name: str) -> BaseParser:
        """Return the parser registered under *name*.

        Args:
            name: Framework name.

        Returns:
            The registered ``BaseParser`` instance.

        Raises:
            KeyError: If no parser is registered for *name*.
        """
        try:
            return self._parsers[name]
        except KeyError:
            available = ", ".join(self._parsers.keys()) or "(none)"
            raise KeyError(
                f"No parser registered for framework '{name}'. "
                f"Available: {available}"
            )

    def supported_frameworks(self) -> List[str]:
        """Return a sorted list of all registered framework names."""
        return sorted(self._parsers.keys())
