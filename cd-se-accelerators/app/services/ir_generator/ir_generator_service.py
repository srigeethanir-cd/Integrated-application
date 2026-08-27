"""
IR Generator Service – Module 4.

Orchestrates the conversion of Module 3 parser output into a framework-agnostic IR.
Uses MapperRegistry to select the appropriate IR mapper, performs thorough validation,
logs metrics, and returns the validated FrameworkAgnosticIR instance.
"""

import logging
from typing import Any, Dict, List, Union

from app.models.analyzer_models import AnalyzerResponse
from app.models.ir_models import FrameworkAgnosticIR
from app.services.ir_generator.angular_mapper import AngularIRMapper
from app.services.ir_generator.mapper_registry import MapperRegistry
from app.services.ir_generator.react_mapper import ReactIRMapper

logger = logging.getLogger(__name__)


def _build_default_mapper_registry() -> MapperRegistry:
    """Instantiate and populate default framework mappers."""
    registry = MapperRegistry()
    registry.register("React", ReactIRMapper())
    registry.register("Angular", AngularIRMapper())
    return registry


class IRGeneratorService:
    """Service orchestrating IR generation, mapping, and validation."""

    def __init__(self, registry: MapperRegistry | None = None) -> None:
        self._registry = registry or _build_default_mapper_registry()
        logger.info(
            "IRGeneratorService initialised – supported mappers: %s",
            self._registry.supported_frameworks(),
        )

    def generate_ir(
        self,
        analyzer_output: Union[AnalyzerResponse, Dict[str, Any]],
        project_name: str = "IngestedProject",
    ) -> FrameworkAgnosticIR:
        """Convert Module 3 output into a validated FrameworkAgnosticIR.

        Args:
            analyzer_output: AnalyzerResponse model instance or raw dictionary.
            project_name: Optional project identifier name.

        Returns:
            Validated ``FrameworkAgnosticIR`` object.

        Raises:
            ValueError: If mapping or IR validation fails.
            KeyError: If no mapper is registered for the detected framework.
        """
        logger.info("IRGeneratorService: Starting IR generation process")

        # Normalize input to dictionary
        if isinstance(analyzer_output, AnalyzerResponse):
            data_dict = analyzer_output.model_dump()
        elif isinstance(analyzer_output, dict):
            data_dict = analyzer_output
        else:
            raise ValueError("Input to IRGeneratorService must be an AnalyzerResponse or dict.")

        framework = data_dict.get("framework", "Unknown")
        logger.info("Detected framework for IR mapping: %s", framework)

        if framework == "Unknown":
            raise ValueError("Cannot generate IR for an 'Unknown' framework.")

        # Select mapper using MapperRegistry
        mapper = self._registry.get_mapper(framework)
        logger.info("Selected IR mapper: %s", mapper.framework_name)

        # Generate IR
        try:
            ir = mapper.map_to_ir(data_dict, project_name=project_name)
        except Exception as exc:
            logger.exception("Error during framework IR mapping: %s", exc)
            raise ValueError(f"IR mapping failed: {exc}") from exc

        # Validate IR
        self.validate_ir(ir)

        # Cache IR for downstream mappers/generators
        from app.utils.ir_cache import cache_ir
        cache_ir(ir)

        logger.info(
            "IR generation complete for project '%s' (%s): %d components, %d elements, %d events, %d services",
            ir.project_name,
            ir.framework,
            len(ir.components),
            len(ir.elements),
            len(ir.events),
            len(ir.services),
        )
        return ir

    def validate_ir(self, ir: FrameworkAgnosticIR) -> None:
        """Perform validation checks on the generated FrameworkAgnosticIR.

        Validates:
        - Component count / presence
        - Component uniqueness (duplicate component names & file paths)
        - Event validity (non-empty name and event_type)
        - Service validity (non-empty service name)
        - Route validity (non-empty route path)
        - Dependency validity (non-empty source)

        Raises:
            ValueError: If validation rules are violated.
        """
        logger.info("IRGeneratorService: Validating FrameworkAgnosticIR")

        # 1. Missing / Empty Components Check
        if not ir.components and not ir.routes and not ir.services:
            logger.warning("IR Validation warning: Project contains no components, services, or routes.")

        # 2. Duplicate Components Check
        seen_components = set()
        duplicates = []
        for comp in ir.components:
            key = (comp.name, comp.file_path)
            if key in seen_components:
                duplicates.append(f"{comp.name} ({comp.file_path})")
            else:
                seen_components.add(key)

        if duplicates:
            msg = f"Duplicate components detected in IR: {', '.join(duplicates)}"
            logger.error(msg)
            raise ValueError(msg)

        # 3. Invalid Events Check
        for ev in ir.events:
            if not ev.name or not ev.event_type:
                msg = f"Invalid UI Event detected: name='{ev.name}', type='{ev.event_type}'"
                logger.error(msg)
                raise ValueError(msg)

        # 4. Invalid Services Check
        for svc in ir.services:
            if not svc.name:
                msg = "Invalid ServiceDependency detected: service name is empty."
                logger.error(msg)
                raise ValueError(msg)

        # 5. Invalid Routes Check
        for r in ir.routes:
            if r.path is None:
                msg = "Invalid RouteModel detected: route path cannot be None."
                logger.error(msg)
                raise ValueError(msg)

        # 6. Invalid Dependencies Check
        for dep in ir.dependencies:
            if not dep.get("source"):
                msg = "Invalid dependency detected: source module is missing."
                logger.error(msg)
                raise ValueError(msg)

        logger.info("IR Validation passed successfully.")
