"""Exercise the real Stage 1-5 and runtime APIs for all acceptance fixtures."""

from __future__ import annotations

import json
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parent
BASE_URL = "http://127.0.0.1:8002"
REPOSITORIES = (
    "basic_crud",
    "banking",
    "ecommerce",
    "validation_heavy",
    "exceptions",
    "file_upload",
    "relationships",
    "jwt_auth",
)


def request(client: httpx.Client, method: str, path: str, **kwargs) -> dict:
    response = client.request(method, f"{BASE_URL}{path}", **kwargs)
    try:
        payload = response.json()
    except ValueError:
        payload = {"raw": response.text}
    if response.is_error:
        raise RuntimeError(
            f"{method} {path} returned {response.status_code}: {payload}"
        )
    return payload


summary_path = ROOT / "pipeline-summary.json"
summary = (
    json.loads(summary_path.read_text(encoding="utf-8"))
    if summary_path.exists() else {}
)
with httpx.Client(timeout=httpx.Timeout(900.0)) as client:
    for name in REPOSITORIES:
        state = summary.get(name, {"repository": name})
        summary[name] = state
        state.pop("error", None)
        try:
            project_id = state.get("project_id")
            if project_id is None:
                archive = ROOT / f"{name}.zip"
                with archive.open("rb") as stream:
                    project = request(
                        client,
                        "POST",
                        "/projects/upload",
                        data={
                            "name": f"stage3-acceptance-{name}",
                            "description": "Stage 3A final acceptance validation",
                        },
                        files={
                            "uploaded_file": (
                                archive.name, stream, "application/zip"
                            )
                        },
                    )
                project_id = project["id"]
                state["project_id"] = project_id

            dependency = state.get("dependency")
            if dependency is None:
                dependency = request(
                    client, "POST", f"/projects/{project_id}/dependencies"
                )
                state["dependency"] = dependency
            dependency_run_id = dependency["run_id"]

            security = state.get("security")
            if security is None:
                security = request(
                    client, "POST", f"/projects/{project_id}/security-scans"
                )
                state["security"] = security

            stage3_path = ROOT / f"{name}-stage3.json"
            if state.get("stage3", {}).get("run_id") and stage3_path.exists():
                run_id = state["stage3"]["run_id"]
            else:
                understanding = request(
                    client,
                    "POST",
                    f"/projects/{project_id}/understand",
                    json={"dependency_run_id": dependency_run_id},
                )
                state["stage3"] = {
                    key: understanding.get(key)
                    for key in (
                        "run_id", "status", "failed_stage", "failure_reason",
                        "last_successful_stage",
                    )
                }
                run_id = understanding["run_id"]
                stage3_path.write_text(
                    json.dumps(understanding["result"], indent=2),
                    encoding="utf-8",
                )

            stage4_path = ROOT / f"{name}-stage4.json"
            if stage4_path.exists():
                generation = json.loads(stage4_path.read_text(encoding="utf-8"))
            else:
                generation = request(
                    client,
                    "POST",
                    f"/projects/{project_id}/generate-test-cases",
                    json={"code_understanding_run_id": run_id},
                )
                stage4_path.write_text(
                    json.dumps(generation, indent=2), encoding="utf-8"
                )
            test_cases = generation.get(
                "generated_test_cases", generation.get("test_cases", [])
            )
            state["stage4"] = {
                "status": "completed",
                "test_cases": len(test_cases),
            }

            stage5_path = ROOT / f"{name}-stage5.json"
            if stage5_path.exists():
                verification = json.loads(
                    stage5_path.read_text(encoding="utf-8")
                )
            else:
                verification = request(
                    client,
                    "POST",
                    f"/projects/{project_id}/verify-test-cases",
                    json={
                        "code_understanding_run_id": run_id,
                        "test_cases": test_cases,
                    },
                )
                stage5_path.write_text(
                    json.dumps(verification, indent=2), encoding="utf-8"
                )
            state["stage5"] = {
                "status": "completed",
                "verified": sum(
                    item.get("status") == "Verified"
                    for item in verification.get("results", [])
                ),
                "total": len(verification.get("results", [])),
            }

            quality_path = ROOT / f"{name}-quality.json"
            if quality_path.exists():
                quality = json.loads(quality_path.read_text(encoding="utf-8"))
            else:
                quality = request(
                    client,
                    "POST",
                    f"/projects/{project_id}/optimize-test-quality",
                    json={
                        "code_understanding_run_id": run_id,
                        "test_cases": test_cases,
                        "verification": verification,
                    },
                )
                quality_path.write_text(
                    json.dumps(quality, indent=2), encoding="utf-8"
                )
            state["quality_prerequisite"] = {
                "status": quality.get("processing_status"),
                "score": quality.get("final_quality_score"),
            }

            runtime = request(
                client,
                "POST",
                f"/projects/{project_id}/runtime-validation",
                json={
                    "code_understanding_run_id": run_id,
                    "base_url": "http://127.0.0.1:8001",
                    "timeout_seconds": 180,
                },
            )
            state["runtime"] = runtime
            if runtime.get("run_id"):
                state["runtime_report"] = request(
                    client,
                    "GET",
                    f"/runtime-validations/{runtime['run_id']}/report",
                )
        except Exception as error:
            state["error"] = str(error)
        finally:
            summary_path.write_text(
                json.dumps(summary, indent=2), encoding="utf-8"
            )

print(json.dumps(summary, indent=2))
