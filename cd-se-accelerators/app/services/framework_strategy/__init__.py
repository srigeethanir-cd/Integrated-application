"""
Framework Strategy Package – Pluggable strategy and registry for multi-framework support.
"""

from app.services.framework_strategy.base_framework_strategy import BaseFrameworkStrategy
from app.services.framework_strategy.framework_registry import (
    FrameworkRegistry,
    build_default_framework_registry,
)
from app.services.framework_strategy.react_strategy import ReactStrategy
from app.services.framework_strategy.angular_strategy import AngularStrategy

__all__ = [
    "BaseFrameworkStrategy",
    "FrameworkRegistry",
    "build_default_framework_registry",
    "ReactStrategy",
    "AngularStrategy",
]
