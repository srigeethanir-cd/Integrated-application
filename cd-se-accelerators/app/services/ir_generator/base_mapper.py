"""
Base IR Mapper Interface – Module 4.

Defines the contract for framework-specific IR mappers. Concrete subclasses
must implement ``map_to_ir()`` to convert framework-specific parser output
into a normalized ``FrameworkAgnosticIR``.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict
from app.models.ir_models import FrameworkAgnosticIR


class BaseIRMapper(ABC):
    """Abstract Strategy interface for mapping framework analysis to IR."""

    @property
    @abstractmethod
    def framework_name(self) -> str:
        """Human-readable framework name targeted by this mapper."""
        ...

    @abstractmethod
    def map_to_ir(self, analysis_data: Dict[str, Any], project_name: str = "IngestedProject") -> FrameworkAgnosticIR:
        """Convert framework-specific parser dictionary into a normalized IR.

        Args:
            analysis_data: Parsed output dictionary from Module 3.
            project_name: Project identifier string.

        Returns:
            Normalized ``FrameworkAgnosticIR`` instance.
        """
        ...
