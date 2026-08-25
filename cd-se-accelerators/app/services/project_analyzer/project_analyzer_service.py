"""
Project Analyzer Service – Module 3 orchestrator.

This is the **single entry point** for project analysis.  It:

1. Validates the project path.
2. Auto-detects the framework via ``FrameworkDetectorService`` (Module 2).
3. Looks up the correct parser from ``ParserRegistry``.
4. Delegates parsing and validates the raw output via Pydantic.
5. Returns a typed ``AnalyzerResponse``.

No if/else chains – framework → parser mapping is handled entirely by the
registry.  Next.js is mapped to the React parser since it is React-based.
"""

from typing import Optional, Any, Dict, List
import logging
import os
from pathlib import Path

from app.models.analyzer_models import (
    AnalyzerResponse,
    AngularAnalysisResult,
    ReactAnalysisResult,
)
from app.services.framework_detection.framework_detector_service import (
    FrameworkDetectorService,
)
from app.services.project_analyzer.angular_parser import AngularParser
from app.services.project_analyzer.parser_registry import ParserRegistry
from app.services.project_analyzer.react_parser import ReactParser

from app.utils.input_preprocessor import get_project_workspace

logger = logging.getLogger(__name__)

# Framework names that should be handled by the React parser.
_REACT_FAMILY = {"React", "Next.js"}


def _build_default_registry() -> ParserRegistry:
    """Create and populate the default parser registry."""
    registry = ParserRegistry()
    registry.register("React", ReactParser())
    registry.register("Angular", AngularParser())
    return registry


class ProjectAnalyzerService:
    """Orchestrates the full Module 3 pipeline:
    detect framework → select parser → parse → validate → respond."""

    def __init__(
        self,
        detector: FrameworkDetectorService | None = None,
        registry: ParserRegistry | None = None,
    ) -> None:
        self._detector = detector or FrameworkDetectorService()
        self._registry = registry or _build_default_registry()
        logger.info(
            "ProjectAnalyzerService initialised – supported frameworks: %s",
            self._registry.supported_frameworks(),
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def analyze(
        self,
        project_path: str,
        project_index: Optional[Any] = None,
        cache_manager: Optional[Any] = None,
    ) -> AnalyzerResponse:
        """Analyse the project at *project_path*.

        Args:
            project_path: Absolute path to the project source directory or ZIP archive.
            project_index: Optional pre-scanned ProjectIndex object.
            cache_manager: Optional AnalysisCacheManager for file-level caching.

        Returns:
            An ``AnalyzerResponse`` with framework-specific analysis data.
        """
        with get_project_workspace(project_path) as path:
            # Step 1: Framework detection (use project_index if provided)
            if project_index and getattr(project_index, "framework", None) and project_index.framework != "Unknown":
                framework = project_index.framework
                logger.info("Using framework from ProjectIndex: %s", framework)
            else:
                detection = self._detector.detect(str(path))
                framework = detection["framework"]
                logger.info(
                    "Framework detected: %s (confidence=%d)",
                    framework,
                    detection.get("confidence", 0),
                )

            if framework == "Unknown":
                raise ValueError(
                    "Unsupported or unrecognised framework. "
                    "Supported: " + ", ".join(self._registry.supported_frameworks())
                )

            # Step 2: Resolve parser key (Next.js → React)
            parser_key = "React" if framework in _REACT_FAMILY else framework

            # Step 3: Look up parser from registry
            try:
                parser = self._registry.get_parser(parser_key)
            except KeyError as exc:
                raise ValueError(str(exc)) from exc

            logger.info(
                "Using parser '%s' for framework '%s'", parser.framework_name, framework
            )

            # Step 4: Always run full parser to discover ALL components
            # The Node.js Babel parser performs comprehensive AST analysis and
            # discovers every component in the project. We never short-circuit
            # this step based on the scanner's component list, which is only
            # a heuristic pre-classification.
            raw_result = parser.parse(path)

            parser_comp_count = len(raw_result.get("components", []))
            scanner_comp_count = len(getattr(project_index, "components", []) or []) if project_index else 0

            logger.info(
                "Full parser completed: discovered %d component(s) "
                "(scanner pre-classified %d potential component files)",
                parser_comp_count,
                scanner_comp_count,
            )

            # Step 4b: Merge any previously cached components that the parser may have missed
            proj_id = getattr(project_index, "project_id", None) if project_index else None
            if project_index and cache_manager and hasattr(project_index, "components"):
                cached_components = []
                for comp in project_index.components:
                    f_path = comp.get("file_path", "")
                    f_hash = comp.get("file_hash", "")
                    cached = cache_manager.get(f_path, f_hash, framework, project_id=proj_id)
                    if cached:
                        cached_components.append(cached)

                if cached_components:
                    existing_comps = raw_result.get("components", [])
                    existing_comp_names = {c.get("name") for c in existing_comps}
                    merged_count = 0
                    for cc in cached_components:
                        if cc.get("name") not in existing_comp_names:
                            existing_comps.append(cc)
                            existing_comp_names.add(cc.get("name"))
                            merged_count += 1
                    raw_result["components"] = existing_comps
                    if merged_count > 0:
                        logger.info(
                            "Merged %d cached component(s) not found by parser",
                            merged_count,
                        )

            # Step 5: Post-process enrichment, path normalization, deduplication & gap analysis
            raw_result = self._enrich_and_normalize_result(raw_result, parser_key)

            # Update cache for fresh analysis entries
            if cache_manager and project_index and hasattr(project_index, "file_hashes"):
                file_hashes = project_index.file_hashes
                for comp in raw_result.get("components", []):
                    f_path = comp.get("file_path", "")
                    f_hash = file_hashes.get(f_path, "")
                    if f_hash and f_path:
                        cache_manager.set(f_path, f_hash, framework, comp, project_id=proj_id)

            # Step 6: Validate via Pydantic
            analysis = self._validate_result(parser_key, raw_result)
            files_analyzed = raw_result.get("files_analyzed", 0)
            final_comp_count = len(raw_result.get("components", []))

            # Coverage validation: compare scanner inventory vs analyzed components
            if project_index:
                scanner_source_files = len(getattr(project_index, "source_files", []) or [])
                logger.info(
                    "Coverage check: scanner_source_files=%d, scanner_components=%d, "
                    "parser_discovered=%d, final_components=%d, files_analyzed=%d",
                    scanner_source_files,
                    scanner_comp_count,
                    parser_comp_count,
                    final_comp_count,
                    files_analyzed,
                )
                if final_comp_count == 0 and scanner_comp_count > 0:
                    logger.warning(
                        "COVERAGE WARNING: Scanner found %d potential component files "
                        "but parser discovered 0 components. Check parser compatibility.",
                        scanner_comp_count,
                    )

            logger.info(
                "Analysis complete: framework=%s, files=%d, components=%d",
                framework,
                files_analyzed,
                final_comp_count,
            )

            return AnalyzerResponse(
                framework=framework,
                project_path=project_path,
                files_analyzed=files_analyzed,
                analysis=analysis,
            )

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _enrich_and_normalize_result(raw_result: dict, parser_key: str) -> dict:
        """Enrich, deduplicate, normalize paths, and sort analysis result for deterministic output."""
        components = raw_result.get("components", [])
        services = raw_result.get("services", [])
        modules = raw_result.get("modules", [])
        existing_tests = raw_result.get("existing_tests", [])
        test_mapping = raw_result.get("test_mapping", [])
        relationships = raw_result.get("component_relationships", [])
        dep_graph = raw_result.get("dependency_graph", [])

        # 1. Path Normalization to POSIX format
        for comp in components:
            if "file_path" in comp and comp["file_path"]:
                comp["file_path"] = comp["file_path"].replace("\\", "/")
        for svc in services:
            if "file_path" in svc and svc["file_path"]:
                svc["file_path"] = svc["file_path"].replace("\\", "/")
        for mod in modules:
            if "file_path" in mod and mod["file_path"]:
                mod["file_path"] = mod["file_path"].replace("\\", "/")
        for t in existing_tests:
            if "file_path" in t and t["file_path"]:
                t["file_path"] = t["file_path"].replace("\\", "/")
        for tm in test_mapping:
            if tm.get("test_file"):
                tm["test_file"] = tm["test_file"].replace("\\", "/")

        # 2. Deduplicate components by (name, file_path)
        seen_comps = set()
        dedup_components = []
        for c in components:
            key = (c.get("name"), c.get("file_path"))
            if key not in seen_comps:
                seen_comps.add(key)
                dedup_components.append(c)
        components = dedup_components
        raw_result["components"] = components

        # 3. Component enrichment (defaults & heuristics)
        for c in components:
            name = c.get("name", "Component")
            name_lower = name.lower()

            # Business Purpose
            if not c.get("business_purpose"):
                if any(k in name_lower for k in ["login", "auth", "signin", "register", "signup"]):
                    c["business_purpose"] = "User Authentication & Access Management"
                elif any(k in name_lower for k in ["card", "stat", "badge", "item", "tile", "counter"]):
                    c["business_purpose"] = "UI Data Card & Metric Presentation"
                elif any(k in name_lower for k in ["form", "input", "editor"]):
                    c["business_purpose"] = "Interactive Form & Data Entry Management"
                elif any(k in name_lower for k in ["nav", "header", "footer", "sidebar", "menu"]):
                    c["business_purpose"] = "Navigation & Page Workspace Layout"
                elif any(k in name_lower for k in ["table", "list", "grid"]):
                    c["business_purpose"] = "Tabular Data & List Collection Presentation"
                else:
                    c["business_purpose"] = "Interactive Frontend Component"

            # Complexity Score & Priority
            props_cnt = len(c.get("props", []) or c.get("inputs", []))
            state_cnt = len(c.get("state", []))
            hooks_cnt = len(c.get("hooks", []))
            handlers_cnt = len(c.get("event_handlers", []))
            api_cnt = len(c.get("api_calls", []))
            forms_cnt = len(c.get("forms", []) or c.get("reactive_forms", []))
            cond_cnt = len(c.get("conditional_rendering", []))

            score = 1 + props_cnt + (state_cnt * 2) + hooks_cnt + handlers_cnt + (api_cnt * 2) + (forms_cnt * 2) + cond_cnt
            c["complexity_score"] = min(10, score)

            risk = 1 + (forms_cnt * 2) + (api_cnt * 2) + state_cnt + hooks_cnt
            c["risk_score"] = min(10, risk)

            if c["complexity_score"] >= 5 or forms_cnt > 0 or api_cnt > 0:
                c["test_priority"] = "high"
            elif handlers_cnt > 0 or state_cnt > 0:
                c["test_priority"] = "medium"
            else:
                c["test_priority"] = "low"

            c.setdefault("confidence_score", 1.0)
            c.setdefault("conditional_rendering", [])
            c.setdefault("event_flows", [])

        # 4. Coverage Analysis & Gaps
        all_comp_names = {c["name"] for c in components if "name" in c}
        tested_comp_names = {tm["component"] for tm in test_mapping if tm.get("test_file")}

        uncovered = sorted(list(all_comp_names - tested_comp_names))
        raw_result["uncovered_components"] = uncovered

        coverage_gaps = []
        for c in components:
            c_name = c.get("name")
            if c_name in uncovered:
                coverage_gaps.append(f"Component '{c_name}' has no unit test file.")
            elif c_name in tested_comp_names:
                tm = next((t for t in test_mapping if t["component"] == c_name), None)
                if tm and not tm.get("covered_features"):
                    coverage_gaps.append(f"Component '{c_name}' has a test file but no covered scenarios detected.")
        raw_result["coverage_gaps"] = sorted(coverage_gaps)

        # 5. Duplicate Tests Detection
        seen_test_files = {}
        dupes = set()
        for tm in test_mapping:
            tf = tm.get("test_file")
            if tf:
                if tf in seen_test_files and seen_test_files[tf] != tm.get("component"):
                    dupes.add(tf)
                else:
                    seen_test_files[tf] = tm.get("component")
        raw_result["duplicate_tests"] = sorted(list(dupes))

        # 6. Deduplicate & Sort Top-Level Collections for Deterministic JSON
        raw_result["components"] = sorted(components, key=lambda x: (x.get("name", ""), x.get("file_path", "")))
        if "services" in raw_result:
            raw_result["services"] = sorted(raw_result["services"], key=lambda x: x.get("name", ""))
        if "modules" in raw_result:
            raw_result["modules"] = sorted(raw_result["modules"], key=lambda x: x.get("name", ""))

        seen_rel = set()
        dedup_rel = []
        for r in relationships:
            key = (r.get("component"), r.get("parent"))
            if key not in seen_rel:
                seen_rel.add(key)
                dedup_rel.append(r)
        raw_result["component_relationships"] = sorted(dedup_rel, key=lambda x: (x.get("component", ""), x.get("depth", 0)))

        seen_dep = set()
        dedup_dep = []
        for d in dep_graph:
            key = d.get("component")
            if key and key not in seen_dep:
                seen_dep.add(key)
                dedup_dep.append(d)
        raw_result["dependency_graph"] = sorted(dedup_dep, key=lambda x: x.get("component", ""))
        raw_result["test_mapping"] = sorted(test_mapping, key=lambda x: x.get("component", ""))

        return raw_result

    @staticmethod
    def _validate_path(path: Path) -> None:
        """Ensure *path* exists and is a directory."""
        if not path.exists():
            raise ValueError(f"Project path does not exist: {path}")
        if not path.is_dir():
            raise ValueError(f"Project path is not a directory: {path}")

    @staticmethod
    def _validate_result(
        parser_key: str, raw: dict
    ) -> ReactAnalysisResult | AngularAnalysisResult:
        """Deserialise the raw parser dict into the correct Pydantic model.

        Raises ``ValueError`` if the data does not match the expected schema.
        """
        try:
            if parser_key == "React":
                return ReactAnalysisResult.model_validate(raw)
            elif parser_key == "Angular":
                return AngularAnalysisResult.model_validate(raw)
            else:
                raise ValueError(f"No Pydantic model for parser key: {parser_key}")
        except Exception as exc:
            logger.error("Result validation failed for %s: %s", parser_key, exc)
            raise ValueError(
                f"Parser output validation failed: {exc}"
            ) from exc
