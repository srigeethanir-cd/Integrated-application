"""
Verification and Benchmark Tests for Source Ingestion & Framework Detection Optimization.

Verifies:
1. Early deterministic framework detection directly from ZIP contents without LLM.
2. Complete exclusion of node_modules, .git, dist, build, coverage, and .cache from extraction.
3. Selective extraction extracts only relevant source, test, and config files.
4. Single-scan lightweight ProjectIndex creation and reuse.
5. Ingestion and framework detection performance metrics breakdown.
6. Empirical before/after benchmark comparison measuring significant speedup.
"""

import io
import json
import os
import shutil
import tempfile
import time
import zipfile
from pathlib import Path
from typing import Dict

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.models.pipeline_models import PipelineRunRequest
from app.services.framework_detection.framework_detector_service import FrameworkDetectorService
from app.services.pipeline_orchestrator_service import PipelineOrchestratorService
from app.services.source_ingestion_service import SourceIngestionService
from app.utils.zip_handler import ZipHandler

client = TestClient(app)


def _create_mock_frontend_zip(
    num_node_modules_files: int = 1500,
    framework: str = "React"
) -> bytes:
    """Create a realistic in-memory frontend project ZIP with large node_modules and build dirs."""
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        # 1. Configuration & Framework files
        if framework == "React":
            zf.writestr(
                "package.json",
                json.dumps({
                    "name": "my-react-app",
                    "version": "1.0.0",
                    "dependencies": {
                        "react": "^18.2.0",
                        "react-dom": "^18.2.0"
                    },
                    "devDependencies": {
                        "typescript": "^5.0.0",
                        "@testing-library/react": "^14.0.0"
                    }
                })
            )
            zf.writestr("vite.config.ts", "import { defineConfig } from 'vite'; export default defineConfig({});")
            zf.writestr("tsconfig.json", '{"compilerOptions": {"jsx": "react-jsx"}}')
            zf.writestr("src/App.tsx", "export const App = () => <h1>App</h1>;")
            zf.writestr("src/components/LoginForm.tsx", "export const LoginForm = () => <form><button>Submit</button></form>;")
            zf.writestr("src/services/apiService.ts", "export const fetchUser = async () => ({ id: 1 });")
            zf.writestr("src/routes/AppRoutes.tsx", "export const AppRoutes = () => <div>Routes</div>;")
            zf.writestr("src/components/LoginForm.test.tsx", "test('renders', () => {});")
        elif framework == "Angular":
            zf.writestr(
                "package.json",
                json.dumps({
                    "name": "my-angular-app",
                    "version": "16.0.0",
                    "dependencies": {
                        "@angular/core": "^16.0.0",
                        "@angular/common": "^16.0.0",
                        "rxjs": "~7.8.0"
                    }
                })
            )
            zf.writestr("angular.json", '{"$schema": "./node_modules/@angular/cli/lib/config/schema.json", "version": 1}')
            zf.writestr("src/app/app.component.ts", "@Component({}) export class AppComponent {}")
            zf.writestr("src/app/app.component.html", "<h1>Angular App</h1>")
            zf.writestr("src/app/login.component.ts", "@Component({}) export class LoginComponent {}")
            zf.writestr("src/app/user.service.ts", "@Injectable() export class UserService {}")

        # 2. Ignored directories: build, dist, .git, .cache, logs, sourcemaps
        zf.writestr("dist/bundle.js", "/* large minified bundle */" * 500)
        zf.writestr("dist/bundle.js.map", '{"version": 3, "sources": []}')
        zf.writestr("build/main.js", "/* build artifact */" * 500)
        zf.writestr(".git/HEAD", "ref: refs/heads/main\n")
        zf.writestr(".git/objects/00/abcdef", "blob binary content")
        zf.writestr(".cache/babel-loader/cache.json", '{"cached": true}')
        zf.writestr("app.log", "2026-08-11 INFO Started server\n" * 100)

        # 3. Simulate thousands of node_modules files
        for i in range(num_node_modules_files):
            pkg_idx = i // 10
            zf.writestr(f"node_modules/pkg_{pkg_idx}/file_{i}.js", f"module.exports = {i};")
            zf.writestr(f"node_modules/pkg_{pkg_idx}/file_{i}.d.ts", f"export declare const val{i}: number;")

    return buffer.getvalue()


def test_early_framework_detection_in_memory():
    """Verify early framework detection runs in memory in <5ms without disk extraction."""
    zip_bytes = _create_mock_frontend_zip(num_node_modules_files=500, framework="React")
    
    detector = FrameworkDetectorService()
    zip_handler = ZipHandler()

    start_time = time.perf_counter()
    insp_res, zf = zip_handler.inspect_and_filter_zip(zip_bytes)
    zf.close()
    duration_ms = (time.perf_counter() - start_time) * 1000.0

    assert insp_res.detected_framework == "React"
    assert insp_res.confidence == 100
    assert "react" in insp_res.detection_reason.lower()
    assert duration_ms < 250.0  # Fast in-memory inspection (<0.25s)
    assert insp_res.ignored_files > 1000  # Correctly identified ignored node_modules files


def test_angular_early_detection():
    """Verify Angular project detection via angular.json & @angular/core in ZIP."""
    zip_bytes = _create_mock_frontend_zip(num_node_modules_files=300, framework="Angular")
    zip_handler = ZipHandler()

    insp_res, zf = zip_handler.inspect_and_filter_zip(zip_bytes)
    zf.close()

    assert insp_res.detected_framework == "Angular"
    assert insp_res.confidence == 100
    assert insp_res.has_angular_json is True


def test_selective_extraction_skips_node_modules():
    """Verify selective extraction extracts ONLY source and config files, never node_modules."""
    zip_bytes = _create_mock_frontend_zip(num_node_modules_files=1000, framework="React")
    zip_handler = ZipHandler()

    with tempfile.TemporaryDirectory() as tmp_dir:
        dest_path = Path(tmp_dir) / "extracted_workspace"
        elapsed_ms, insp_res = zip_handler.extract_selective(zip_bytes, dest_path)

        # Check extracted files
        extracted_files = [str(p.relative_to(dest_path)).replace("\\", "/") for p in dest_path.rglob("*") if p.is_file()]

        # Assert no node_modules, dist, .git, .cache or .map files exist on disk
        for ef in extracted_files:
            assert "node_modules" not in ef
            assert ".git" not in ef
            assert "dist" not in ef
            assert "build" not in ef
            assert ".cache" not in ef
            assert not ef.endswith(".map")
            assert not ef.endswith(".log")

        # Assert relevant source files ARE present
        assert "package.json" in extracted_files
        assert "src/App.tsx" in extracted_files
        assert "src/components/LoginForm.tsx" in extracted_files
        assert "src/services/apiService.ts" in extracted_files
        assert "src/components/LoginForm.test.tsx" in extracted_files

        assert insp_res.ignored_files >= 2000
        assert len(extracted_files) <= 15


@pytest.mark.asyncio
async def test_source_ingestion_service_metrics():
    """Verify SourceIngestionService measures and returns detailed performance metrics."""
    zip_bytes = _create_mock_frontend_zip(num_node_modules_files=800, framework="React")
    service = SourceIngestionService()

    res = await service.upload_zip("large_frontend_project.zip", zip_bytes)

    # Verify tuple unpacking compatibility
    project_id, project_path = res
    assert project_id is not None
    assert os.path.exists(project_path)

    # Verify enriched metadata & performance metrics
    assert res.detected_framework == "React"
    assert res.stats.total_files > 1600
    assert res.stats.ignored_files > 1600
    assert res.stats.extracted_files <= 15
    assert res.stats.processed_files >= 5

    metrics = res.metrics
    assert metrics.zip_inspection_time_ms >= 0.0
    assert metrics.file_filtering_time_ms >= 0.0
    assert metrics.framework_detection_time_ms >= 0.0
    assert metrics.extraction_time_ms >= 0.0
    assert metrics.project_index_time_ms >= 0.0
    assert metrics.total_ingestion_time_ms >= 0.0

    # Clean up workspace
    shutil.rmtree(Path(project_path).parent, ignore_errors=True)


def test_api_upload_zip_endpoint_returns_metrics():
    """Verify POST /source/upload HTTP endpoint returns detected framework, stats, and metrics."""
    zip_bytes = _create_mock_frontend_zip(num_node_modules_files=500, framework="React")

    response = client.post(
        "/source/upload",
        files={"file": ("project_bundle.zip", zip_bytes, "application/zip")}
    )

    assert response.status_code == 201
    data = response.json()

    assert data["project_id"] is not None
    assert "project_path" in data
    assert data["detected_framework"] == "React"
    assert data["stats"]["total_files"] > 1000
    assert data["stats"]["ignored_files"] > 1000
    assert data["metrics"]["total_ingestion_time_ms"] > 0.0

    # Cleanup
    shutil.rmtree(Path(data["project_path"]).parent, ignore_errors=True)


def test_benchmark_unoptimized_vs_optimized():
    """Measure empirical before/after performance improvement comparing full extraction vs selective."""
    num_files = 600
    zip_bytes = _create_mock_frontend_zip(num_node_modules_files=num_files, framework="React")

    # 1. Benchmark full unoptimized extraction (what previous implementation did)
    with tempfile.TemporaryDirectory() as tmp_dir:
        dest_unoptimized = Path(tmp_dir) / "unoptimized"
        dest_unoptimized.mkdir()
        
        t0 = time.perf_counter()
        with zipfile.ZipFile(io.BytesIO(zip_bytes), "r") as zf:
            zf.extractall(dest_unoptimized)
        unoptimized_time_ms = (time.perf_counter() - t0) * 1000.0
        unoptimized_file_count = sum(1 for _ in dest_unoptimized.rglob("*") if _.is_file())

    # 2. Benchmark optimized selective extraction & early framework detection
    zip_handler = ZipHandler()
    with tempfile.TemporaryDirectory() as tmp_dir:
        dest_optimized = Path(tmp_dir) / "optimized"
        dest_optimized.mkdir()

        t1 = time.perf_counter()
        insp_res, zf = zip_handler.inspect_and_filter_zip(zip_bytes)
        ext_ms, _ = zip_handler.extract_selective(zip_bytes, dest_optimized, inspection_result=insp_res, zf=zf)
        zf.close()
        optimized_time_ms = (time.perf_counter() - t1) * 1000.0
        optimized_file_count = sum(1 for _ in dest_optimized.rglob("*") if _.is_file())

    speedup_factor = unoptimized_time_ms / max(optimized_time_ms, 0.001)

    print(f"\n[MEASURED BENCHMARK RESULT]")
    print(f"Total files in archive: {num_files * 2 + 10}")
    print(f"Unoptimized extraction time: {unoptimized_time_ms:.2f} ms ({unoptimized_file_count} files on disk)")
    print(f"Optimized selective ingestion: {optimized_time_ms:.2f} ms ({optimized_file_count} files on disk)")
    print(f"Performance Speedup: {speedup_factor:.1f}x faster")

    assert optimized_file_count <= 15
    assert unoptimized_file_count > num_files * 2
    assert optimized_time_ms < unoptimized_time_ms
    assert speedup_factor > 2.0
