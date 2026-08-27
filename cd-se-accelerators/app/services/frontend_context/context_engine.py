"""
Frontend Context Extraction Engine (FCE) Main Orchestrator.

Main entry point for extracting ground-truth FrontendContext from source code or analysis results.
Includes safe fallback handling to prevent crashing the main pipeline.
"""

import logging
from typing import Any, Dict, List, Optional
from app.services.frontend_context.ast_analyzer import ASTAnalyzer
from app.services.frontend_context.component_analyzer import ComponentAnalyzer
from app.services.frontend_context.context_validator import ContextValidator
from app.services.frontend_context.file_analyzer import compute_file_hash, get_cached_context, set_cached_context
from app.services.frontend_context.models import (
    CompletenessReport,
    FrontendContextResponse,
    SingleComponentFrontendContext,
)

logger = logging.getLogger(__name__)


class FrontendContextEngine:
    """Main orchestrator for Frontend Context Extraction Engine (FCE)."""

    def __init__(self) -> None:
        self._ast_analyzer = ASTAnalyzer()
        self._comp_analyzer = ComponentAnalyzer()
        self._validator = ContextValidator()

    def extract_context(
        self,
        analysis_result: Dict[str, Any],
        project_path: Optional[str] = None,
        project_name: str = "Project",
        project_id: Optional[str] = None,
        pipeline_run_id: Optional[str] = None,
        framework: str = "React",
    ) -> FrontendContextResponse:
        """Extract structured FrontendContext from analysis result or source files with safe fallback."""
        logger.info("FCE: Beginning Frontend Context extraction (project_id=%s)", project_id)

        contexts: List[SingleComponentFrontendContext] = []
        raw_components = analysis_result.get("components") if isinstance(analysis_result, dict) else []

        try:
            for comp in raw_components or []:
                comp_dict = comp if isinstance(comp, dict) else (comp.model_dump() if hasattr(comp, "model_dump") else {})
                comp_name = comp_dict.get("name") or comp_dict.get("component_name") or "Component"
                src_file = comp_dict.get("file_path") or comp_dict.get("source_file") or f"src/{comp_name}.jsx"

                file_hash = compute_file_hash(src_file) if project_path else "hash"
                cached = get_cached_context(project_id or "default", src_file, file_hash) if project_id else None

                if cached:
                    logger.debug("FCE: Cache hit for component %s (%s)", comp_name, src_file)
                    contexts.append(cached)
                else:
                    # Safe component extraction
                    try:
                        ctx = self._comp_analyzer.analyze_component(
                            comp_data=comp_dict,
                            project_id=project_id,
                            pipeline_run_id=pipeline_run_id,
                            framework=framework,
                        )
                        contexts.append(ctx)
                        if project_id:
                            set_cached_context(project_id, src_file, file_hash, ctx)
                    except Exception as exc:
                        logger.warning("FCE: Failed to extract context for component %s: %s. Using fallback.", comp_name, exc)
                        fallback_ctx = SingleComponentFrontendContext(
                            project_id=project_id,
                            pipeline_run_id=pipeline_run_id,
                            component_id=f"comp_{comp_name}",
                            component_name=comp_name,
                            source_file=src_file,
                            framework=framework,
                        )
                        contexts.append(fallback_ctx)

            report = self._validator.validate_and_generate_report(contexts, len(raw_components or []))

            return FrontendContextResponse(
                project_name=project_name,
                project_id=project_id,
                pipeline_run_id=pipeline_run_id,
                framework=framework,
                contexts=contexts,
                completeness_report=report,
            )

        except Exception as exc:
            logger.error("FCE: Critical error during context extraction: %s. Triggering safe fallback.", exc)
            return FrontendContextResponse(
                project_name=project_name,
                project_id=project_id,
                pipeline_run_id=pipeline_run_id,
                framework=framework,
                contexts=[],
                completeness_report=CompletenessReport(components_discovered=0, components_analyzed=0),
            )
