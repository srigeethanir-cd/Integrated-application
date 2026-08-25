"""
Test Writer Service – Module 8.

Orchestrates framework-agnostic test suite compiling, formatting with Prettier,
running validation checks via AST, and exporting the test manifest.
"""

import json
import logging
import os
import subprocess
from datetime import datetime
from typing import Any, Dict, List, Optional, Set, Union

from app.models.test_case_models import TestCase, TestCasePlanResponse
from app.models.test_writer_models import GeneratedTestFile, TestWriterResponse
from app.services.test_writer.react_test_writer import ReactTestWriter
from app.services.test_writer.angular_test_writer import AngularTestWriter
from app.services.test_writer.test_writer_registry import TestWriterRegistry

logger = logging.getLogger(__name__)

# Absolute paths setup
_CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
_VALIDATOR_PATH = os.path.join(_CURRENT_DIR, "validator.js")
_PARSERS_DIR = os.path.abspath(os.path.join(_CURRENT_DIR, "..", "project_analyzer", "parsers"))


def _build_default_registry() -> TestWriterRegistry:
    registry = TestWriterRegistry()
    registry.register(ReactTestWriter())
    registry.register(AngularTestWriter())
    return registry


class TestWriterService:
    """Manages isolated test compilation, Prettier code format, and AST validations."""

    def __init__(self, registry: TestWriterRegistry | None = None) -> None:
        self._registry = registry or _build_default_registry()
        logger.info(
            "TestWriterService initialised with registry: %s",
            ", ".join(w.framework for w in self._registry._writers.values())
        )

    def generate_test_suite(
        self,
        test_case_plan: Union[TestCasePlanResponse, Dict[str, Any]],
        output_workspace_dir: Optional[str] = None,
        pipeline_run_id: Optional[str] = None
    ) -> TestWriterResponse:
        """Process TestCasePlanResponse and compile framework-specific test suites.

        Args:
            test_case_plan: TestCasePlanResponse Pydantic model or dict.
            output_workspace_dir: Optional directory where outputs and manifests are created.
            pipeline_run_id: Optional pipeline run identifier.

        Returns:
            TestWriterResponse detailing summary results.
        """
        logger.info("TestWriterService: Starting test suite generation.")

        output_workspace_dir = output_workspace_dir or "."

        # Normalize test case plan
        if isinstance(test_case_plan, TestCasePlanResponse):
            plan_dict = test_case_plan.model_dump()
        elif hasattr(test_case_plan, "test_case_plan") and getattr(test_case_plan, "test_case_plan"):
            legacy_tcp = getattr(test_case_plan, "test_case_plan")
            plan_dict = legacy_tcp.model_dump() if hasattr(legacy_tcp, "model_dump") else legacy_tcp
        elif isinstance(test_case_plan, dict):
            if "test_case_plan" in test_case_plan:
                plan_dict = test_case_plan["test_case_plan"]
            else:
                plan_dict = test_case_plan
        else:
            raise ValueError("test_case_plan must be a TestCasePlanResponse or dict.")

        framework = plan_dict.get("framework", "")
        project_name = plan_dict.get("project_name", "IngestedProject")

        # Parse test cases
        test_cases: List[TestCase] = []
        for tc_dict in plan_dict.get("test_cases", []):
            test_cases.append(TestCase.model_validate(tc_dict))

        # 1. Validation Checks (prior to code generation)
        validation_errors: List[str] = []
        
        valid_frameworks = {"react", "angular"}
        if framework.lower() not in valid_frameworks:
            validation_errors.append(f"Invalid framework: '{framework}'. Supported values: React, Angular.")

        for tc in test_cases:
            if not tc.component or not tc.component.strip():
                validation_errors.append(f"Validation Error: Test case '{tc.id}' is missing component declaration.")
            if not tc.metadata:
                validation_errors.append(f"Validation Error: Test case '{tc.id}' is missing enriched codegen metadata.")

        if validation_errors:
            logger.error("Validation failed before generation: %s", validation_errors)
            return TestWriterResponse(
                total_files=0,
                generated_files=[],
                manifest_path="",
                validation_passed=False,
                validation_errors=validation_errors
            )

        # Retrieve writer from registry
        writer = self._registry.get_writer(framework)
        if not writer:
            err = f"Unsupported framework writer requested: '{framework}'."
            logger.error(err)
            return TestWriterResponse(
                total_files=0,
                generated_files=[],
                manifest_path="",
                validation_passed=False,
                validation_errors=[err]
            )

        # 2. Output directory mapping (isolated workspace location)
        sub_folder = "react" if framework.lower() == "react" else "angular"
        target_dir = os.path.abspath(os.path.join(output_workspace_dir, "tests", sub_folder))
        os.makedirs(target_dir, exist_ok=True)

        logger.info("Writing test suite files inside isolated directory: %s", target_dir)

        # 3. Call Hybrid LLM Test Writer (Module 8) or Fallback to Deterministic Registry Writer
        raw_files: List[GeneratedTestFile] = []
        try:
            from app.services.test_writer.llm_test_writer import LLMTestWriter
            llm_writer = LLMTestWriter()

            # Group test cases by component
            comp_tc_map: Dict[str, List[TestCase]] = {}
            for tc in test_cases:
                comp_tc_map.setdefault(tc.component or "Component", []).append(tc)

            for comp_name, comp_tcs in comp_tc_map.items():
                llm_file = llm_writer.generate_llm_test_file(
                    component_name=comp_name,
                    test_cases=comp_tcs,
                    framework=framework,
                    workspace_dir=output_workspace_dir,
                )
                if llm_file:
                    full_p = os.path.join(target_dir, llm_file.file_name)
                    llm_file.file_path = full_p
                    raw_files.append(llm_file)

            if raw_files:
                logger.info("Hybrid LLM Layer (Module 8): Generated %d LLM test files.", len(raw_files))
        except Exception as exc:
            logger.warning("Hybrid LLM Layer (Module 8): LLM test writer skipped/fallback: %s", exc)

        if not raw_files:
            logger.info("Module 8 Deterministic Layer: Executing template test writer '%s'.", writer.__class__.__name__)
            raw_files = writer.write(test_cases, target_dir)

        written_files: List[GeneratedTestFile] = []

        # 4. File collision checking & writing
        for f in raw_files:
            file_name = f.file_name
            file_path = f.file_path

            # Existing file detection protection
            if os.path.exists(file_path):
                # Generate unique versioned filename
                base, ext = os.path.splitext(file_name)
                # In React it's .test.tsx, so split accordingly
                if base.endswith(".test"):
                    base_comp = base[:-5]
                    file_name = f"{base_comp}.test.generated{ext}"
                elif base.endswith(".spec"):
                    base_comp = base[:-5]
                    file_name = f"{base_comp}.spec.generated{ext}"
                else:
                    file_name = f"{base}.generated{ext}"
                
                file_path = os.path.join(target_dir, file_name)
                logger.info("File collision detected. Alternative filename registered: %s", file_name)

            # Write code to file
            with open(file_path, "w", encoding="utf-8") as out:
                out.write(f.content)

            # Code Formatting using Prettier
            self._format_file(file_path)

            # Read formatted content back
            with open(file_path, "r", encoding="utf-8") as src:
                formatted_code = src.read()

            written_files.append(
                GeneratedTestFile(
                    file_name=file_name,
                    file_path=file_path,
                    content=formatted_code,
                    test_case_ids=f.test_case_ids,
                    component=f.component,
                    source_file=f.source_file,
                    source_language=f.source_language,
                    source_extension=f.source_extension,
                    test_extension=f.test_extension,
                )
            )

        # 5. AST Compilation Syntax Validation check
        validation_passed = True
        for f in written_files:
            file_errors = self._validate_syntax(f.file_path)
            if file_errors:
                validation_passed = False
                validation_errors.extend([f"Syntax Error in {f.file_name}: {err}" for err in file_errors])

        # 6. Generate Manifest test_manifest.json
        manifest_path = os.path.join(output_workspace_dir, "test_manifest.json")
        manifest_data = {
            "pipeline_run_id": pipeline_run_id or plan_dict.get("pipeline_run_id") or "run_default",
            "generated_at": datetime.now().isoformat() + "Z",
            "framework": framework,
            "total_files": len(written_files),
            "generated_files": []
        }

        # Build generated file manifest links
        for f in written_files:
            comp_cases = list(f.test_case_ids or [])
            comp_name = f.component or "Default"
            src_file = f.source_file

            if not comp_cases or not src_file:
                for tc in test_cases:
                    test_suffix = f.file_name.split(".test")[0].split(".spec")[0]
                    if tc.component == test_suffix or tc.component == comp_name:
                        if tc.id not in comp_cases:
                            comp_cases.append(tc.id)
                        if tc.source_file and not src_file:
                            src_file = tc.source_file

            source_file = src_file or f"src/components/{comp_name}.jsx"
            src_ext = f.source_extension or os.path.splitext(source_file)[1] or ".jsx"
            src_lang = f.source_language or ("TypeScript" if src_ext in [".tsx", ".ts"] else "JavaScript")
            test_ext = f.test_extension or f".test{src_ext}"

            manifest_data["generated_files"].append({
                "component": comp_name,
                "file": f.file_name,
                "file_name": f.file_name,
                "file_path": f"tests/{sub_folder}/{f.file_name}",
                "source_file": source_file,
                "source_language": src_lang,
                "source_extension": src_ext,
                "test_extension": test_ext,
                "framework": framework,
                "test_cases": comp_cases,
                "test_case_ids": comp_cases,
                "generated_at": datetime.now().isoformat() + "Z",
                "pipeline_run_id": pipeline_run_id or plan_dict.get("pipeline_run_id") or "run_default"
            })

        with open(manifest_path, "w", encoding="utf-8") as mf:
            json.dump(manifest_data, mf, indent=2)

        logger.info(
            "Completed test suite generation: %d file(s) generated. Validation passed = %s",
            len(written_files),
            validation_passed
        )

        return TestWriterResponse(
            total_files=len(written_files),
            generated_files=written_files,
            manifest_path=manifest_path,
            validation_passed=validation_passed,
            validation_errors=validation_errors
        )

    def _format_file(self, file_path: str) -> None:
        """Spawn Prettier formatter subprocess."""
        logger.debug("Formatting file with Prettier: %s", file_path)
        try:
            # Try running npx prettier --write
            cmd = ["npx", "prettier", "--write", file_path]
            # Use shell=True for windows command resolutions
            subprocess.run(
                cmd,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=True,
                cwd=_PARSERS_DIR
            )
            logger.debug("Prettier formatted file successfully.")
        except Exception as exc:
            logger.warning(
                "Prettier format failed on %s (checking if Prettier is installed): %s",
                os.path.basename(file_path),
                exc
            )

    def _validate_syntax(self, file_path: str) -> List[str]:
        """Verify typescript/JSX AST structure validity using validator.js."""
        logger.info("Running syntax compilation validation on: %s", os.path.basename(file_path))
        try:
            cmd = ["node", _VALIDATOR_PATH, file_path]
            result = subprocess.run(
                cmd,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=True,
                cwd=_PARSERS_DIR  # run inside parser directory to resolve local node_modules
            )
            
            output_str = result.stdout.decode("utf-8").strip()
            # Find JSON block inside logging output if present
            if "{" in output_str:
                json_start = output_str.find("{")
                json_str = output_str[json_start:]
                report = json.loads(json_str)
                if not report.get("passed", False):
                    return report.get("errors", ["Unknown parsing error"])
            return []
        except Exception as exc:
            msg = f"Validation execution compiler failed: {exc}"
            logger.warning(msg)
            return [msg]
