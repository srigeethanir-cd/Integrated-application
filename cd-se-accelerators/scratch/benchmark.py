import asyncio
import time
from app.models.pipeline_models import PipelineRunRequest
from app.services.pipeline_orchestrator_service import PipelineOrchestratorService


async def main():
    orchestrator = PipelineOrchestratorService()
    req = PipelineRunRequest(
        project_path="scratch/test_workspace/react_large",
        run_until="validation",
        include_timings=True,
        include_intermediate_outputs=True
    )
    
    print("--- RUN 1 (Cold Cache) ---")
    t1_start = time.perf_counter()
    res1 = await orchestrator.run_pipeline(req)
    t1_duration = (time.perf_counter() - t1_start) * 1000.0
    
    print(f"Status: {res1.status}")
    print(f"Total Pipeline Time: {res1.total_execution_time_ms:.2f} ms")
    if res1.performance_metrics:
        pm = res1.performance_metrics
        print(f"Files Scanned: {pm.total_files_scanned}")
        print(f"Relevant Files: {pm.relevant_files}")
        print(f"Ignored Files: {pm.ignored_files}")
        print(f"Cached Files: {pm.cached_files}")
        print(f"Files Analyzed: {pm.files_analyzed}")
        print(f"Cache Hit Rate: {pm.cache_hit_rate:.2f}%")
        print(f"Parallel Tasks: {pm.parallel_tasks}")
        print(f"Scan Time: {pm.project_scan_time_ms:.2f} ms")
        print(f"Analysis Time: {pm.component_analysis_time_ms:.2f} ms")
        
    print("\n--- RUN 2 (Warm Cache) ---")
    t2_start = time.perf_counter()
    res2 = await orchestrator.run_pipeline(req)
    t2_duration = (time.perf_counter() - t2_start) * 1000.0
    
    print(f"Status: {res2.status}")
    print(f"Total Pipeline Time: {res2.total_execution_time_ms:.2f} ms")
    if res2.performance_metrics:
        pm = res2.performance_metrics
        print(f"Cached Files: {pm.cached_files}")
        print(f"Files Analyzed: {pm.files_analyzed}")
        print(f"Cache Hit Rate: {pm.cache_hit_rate:.2f}%")
        print(f"Analysis Time: {pm.component_analysis_time_ms:.2f} ms")


if __name__ == "__main__":
    asyncio.run(main())
