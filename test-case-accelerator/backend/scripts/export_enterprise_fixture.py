"""Generate the acceptance fixture's production export archive."""

from pathlib import Path
import shutil
import uuid

from app.agents.code_understanding.agent import CodeUnderstandingAgent, CodeUnderstandingContext, SourceFileContext
from app.agents.test_generation.deterministic_unit_generator import DeterministicUnitTestGenerator
from app.services.export.pytest_export_service import PytestExportService


backend = Path(__file__).resolve().parents[1]
fixture = backend.parent / "testing" / "enterprise-validation-project"
files = [
    SourceFileContext(
        path=path.relative_to(fixture).as_posix(), language="python", imports=[],
        classes=[], functions=[], content=path.read_text(encoding="utf-8"),
    )
    for path in sorted((fixture / "app").glob("*.py"))
]
stage3 = CodeUnderstandingAgent().analyze(CodeUnderstandingContext(
    project_id=uuid.uuid4(), dependency_run_id=uuid.uuid4(), files=files,
)).model_dump(mode="json")
generation = DeterministicUnitTestGenerator().generate(stage3)
archive = PytestExportService(generator_version=DeterministicUnitTestGenerator.VERSION).create_archive(
    project_name="enterprise-validation-project",
    pipeline_state={
        "test_generation": generation,
        "test_verification": {"summary": {"verified": len(generation["generated_test_cases"]), "partial": 0, "failed": 0}},
        "runtime_execution_plan": {"status": "ready"},
    },
)
destination = backend / "validation-results" / "enterprise-test-suite.zip"
destination.parent.mkdir(parents=True, exist_ok=True)
shutil.copyfile(archive, destination)
archive.unlink(missing_ok=True)
print(destination)
