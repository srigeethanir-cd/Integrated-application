"""
IR Mapper Module Re-exporter – Module 4.

Exports BaseIRMapper, ReactIRMapper, AngularIRMapper, and MapperRegistry.
"""

from app.services.ir_generator.base_mapper import BaseIRMapper
from app.services.ir_generator.react_mapper import ReactIRMapper
from app.services.ir_generator.angular_mapper import AngularIRMapper
from app.services.ir_generator.mapper_registry import MapperRegistry

__all__ = ["BaseIRMapper", "ReactIRMapper", "AngularIRMapper", "MapperRegistry"]
