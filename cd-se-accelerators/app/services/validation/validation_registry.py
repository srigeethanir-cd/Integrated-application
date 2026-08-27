"""
Validation Registry – Module 9.

Maintains registries of concrete framework validators to decouple lookups.
"""

from typing import Dict
from app.services.validation.base_validator import BaseValidator


class ValidationRegistry:
    """Registry to register and fetch framework-specific validators dynamically."""

    def __init__(self) -> None:
        self._validators: Dict[str, BaseValidator] = {}

    def register(self, validator: BaseValidator) -> None:
        """Register a new validator instance."""
        self._validators[validator.framework.lower()] = validator

    def get_validator(self, framework: str) -> BaseValidator | None:
        """Fetch a validator matching the framework name, case-insensitively."""
        return self._validators.get(framework.lower())
