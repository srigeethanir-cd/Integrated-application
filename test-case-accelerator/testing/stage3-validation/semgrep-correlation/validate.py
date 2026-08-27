"""Run the real Semgrep-to-Stage-3 correlation validation."""

from __future__ import annotations

import json
import sys
import uuid
from pathlib import Path
from unittest.mock import Mock

BACKEND_ROOT = Path(__file__).resolve().parents[3] / "backend"
sys.path.insert(0, str(BACKEND_ROOT))

from app.agents.code_understanding.agent import (  # noqa: E402
    CodeUnderstandingContext,
    SourceFileContext,
)
from app.services.code_understanding.static_analyzer import (  # noqa: E402
    PythonStaticAnalyzer,
)
from app.services.security_scan.security_scan_service import (  # noqa: E402
    SecurityScanService,
    SemgrepRunner,
)

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "source"
SEMGREP = BACKEND_ROOT / ".venv" / "Scripts" / "semgrep.exe"

EXPECTED = {
    "validation.python.sql-injection": {
        "file": "app/api.py",
        "functions": ["unsafe_user_lookup"],
        "classes": [],
        "endpoints": ["GET /tools/users"],
    },
    "validation.python.eval": {
        "file": "app/api.py",
        "functions": ["evaluate_expression"],
        "classes": [],
        "endpoints": ["POST /tools/evaluate"],
    },
    "validation.python.dangerous-subprocess": {
        "file": "app/commands.py",
        "functions": ["execute"],
        "classes": ["CommandRunner"],
        "endpoints": [],
    },
    "validation.python.weak-cryptography": {
        "file": "app/crypto.py",
        "functions": ["digest"],
        "classes": ["TokenHasher"],
        "endpoints": [],
    },
    "validation.python.hardcoded-secret": {
        "file": "app/secrets.py",
        "functions": ["load_partner_credentials"],
        "classes": [],
        "endpoints": [],
    },
}


def short_rule(rule_id: str) -> str:
    return next(key for key in EXPECTED if rule_id.endswith(key))


payload = SemgrepRunner(
    executable=str(SEMGREP),
    config=str(ROOT / "rules.yml"),
    timeout_seconds=120,
).scan(SOURCE)
normalized = SecurityScanService(
    Mock(), Mock(), Mock(), Mock()
)._findings(payload, SOURCE)
findings = [
    {"id": f"finding-{index}", **finding}
    for index, finding in enumerate(
        sorted(normalized, key=lambda item: (
            item["file"], item["line"], item["rule_id"]
        )),
        start=1,
    )
]
files = [
    SourceFileContext(
        path=path.relative_to(SOURCE).as_posix(),
        language="python",
        content=path.read_text(encoding="utf-8"),
    )
    for path in sorted(SOURCE.rglob("*.py"))
]
context = CodeUnderstandingContext(
    project_id=uuid.UUID(int=1),
    dependency_run_id=uuid.UUID(int=2),
    files=files,
    security_findings=findings,
)
first = PythonStaticAnalyzer().analyze(context)
second = PythonStaticAnalyzer().analyze(context)

rows = []
for finding in first.security_findings:
    rule = short_rule(finding.rule_id)
    attached_functions = sorted(
        item.name for item in first.functions
        if any(match.id == finding.id for match in item.security_findings)
    )
    attached_classes = sorted(
        item.name for item in first.classes
        if any(match.id == finding.id for match in item.security_findings)
    )
    attached_endpoints = sorted(
        f"{item.method} {item.route}" for item in first.api_endpoints
        if any(match.id == finding.id for match in item.security_findings)
    )
    actual = {
        "file": finding.file,
        "functions": attached_functions,
        "classes": attached_classes,
        "endpoints": attached_endpoints,
    }
    rows.append({
        "rule": rule,
        **actual,
        "expected": EXPECTED[rule],
        "status": "PASS" if actual == EXPECTED[rule] else "FAIL",
    })

report = {
    "semgrep_findings": len(normalized),
    "stage3_findings": len(first.security_findings),
    "deterministic": (
        first.model_dump(mode="json") == second.model_dump(mode="json")
    ),
    "rows": sorted(rows, key=lambda item: item["rule"]),
}
report["passed"] = (
    report["semgrep_findings"] == len(EXPECTED)
    and report["stage3_findings"] == len(EXPECTED)
    and report["deterministic"]
    and all(item["status"] == "PASS" for item in report["rows"])
)
print(json.dumps(report, indent=2))
raise SystemExit(0 if report["passed"] else 1)
