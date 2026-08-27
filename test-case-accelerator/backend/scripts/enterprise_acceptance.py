"""Repeatable deterministic acceptance run for the enterprise validation fixture."""

from __future__ import annotations

import json
from pathlib import Path
import sys
import uuid

from app.agents.code_understanding.agent import CodeUnderstandingAgent, CodeUnderstandingContext, SourceFileContext
from app.agents.semantic_verification.agent import TestVerificationAgent
from app.agents.test_generation.test_generation_agent import TestGenerationAgent
from app.schemas.test_case import TestCase
from app.services.runtime.execution_manager import ExecutionManager
from app.services.runtime.pytest_runner import PytestRunner
from app.services.runtime.report_generator import ReportGenerator
from app.services.runtime.result_collector import ResultCollector
from app.services.runtime.runtime_preparation_service import RuntimePreparationService
from app.services.runtime.test_file_builder import TestFileBuilder


def main() -> int:
    backend = Path(__file__).resolve().parents[1]
    fixture = backend.parent / "testing" / "enterprise-validation-project"
    sources = []
    source_context = []
    for path in sorted((fixture / "app").glob("*.py")):
        content = path.read_text(encoding="utf-8")
        relative = path.relative_to(fixture).as_posix()
        sources.append({"path": relative, "content": content})
        source_context.append(SourceFileContext(
            path=relative,
            language="python",
            imports=[],
            classes=[],
            functions=[],
            content=content,
        ))

    context = CodeUnderstandingContext(
        project_id=uuid.uuid4(),
        dependency_run_id=uuid.uuid4(),
        files=source_context,
    )
    understanding = CodeUnderstandingAgent().analyze(context)
    stage3 = understanding.model_dump(mode="json")
    generation = TestGenerationAgent(deterministic_mode=True).generate(stage3)
    cases = [TestCase.model_validate(item) for item in generation["generated_test_cases"]]
    verification = TestVerificationAgent(rule_confidence_threshold=0).verify(cases, stage3, sources)
    plan = RuntimePreparationService().prepare(cases, stage3)
    outcome = ExecutionManager(TestFileBuilder(), PytestRunner(), ResultCollector(), ReportGenerator()).execute(
        source_directory=fixture,
        test_cases=plan.targets,
        base_url="",
        timeout_seconds=120,
    )

    targets = stage3.get("test_targets", [])
    symbols = [target["symbol"] for target in targets]
    canonical_targets = [
        str(target.get("qualified_name") or f"{target.get('file')}:{target['symbol']}")
        for target in targets
    ]
    duplicates = len(canonical_targets) - len(set(canonical_targets))
    report = {
        "fixture": str(fixture),
        "python_files": len(source_context),
        "functions": len(stage3.get("functions", [])),
        "classes": len(stage3.get("classes", [])),
        "api_endpoints": len(stage3.get("api_endpoints", [])),
        "targets": len(symbols),
        "duplicate_targets": duplicates,
        "repeated_unqualified_names": len(symbols) - len(set(symbols)),
        "generated_tests": len(cases),
        "duplicate_test_ids": len(cases) - len({case.id for case in cases}),
        "verification": verification.get("summary", {}),
        "runtime_preparation": {
            "prepared": plan.prepared_tests,
            "unresolved": plan.unresolved_tests,
            "issues": [issue.model_dump(mode="json") for issue in plan.issues],
        },
        "runtime": outcome.summary,
        "runtime_results": outcome.results,
    }
    output = backend / "validation-results" / "enterprise-acceptance.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
    print(json.dumps({key: value for key, value in report.items() if key != "runtime_results"}, indent=2, default=str))
    return 0 if outcome.summary.get("failed", 0) == 0 and outcome.summary.get("not_executable", 0) == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
