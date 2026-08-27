import time
import logging
from typing import Dict, Any, List, Set, Callable
from concurrent.futures import ThreadPoolExecutor, as_completed
from sqlalchemy.orm import Session
from app.models import ExecutionTimelineRecord, AgentExecutionMetric

logger = logging.getLogger(__name__)

class StoryExecutionScheduler:
    """Orchestrates story generation task queue scheduling and parallel executions using PostgreSQL state."""

    def __init__(self, db: Session, project_id: str, max_workers: int = 4):
        self.db = db
        self.project_id = project_id
        self.max_workers = max_workers

    def load_state(self, stories: List[Dict[str, Any]], execution_order: List[str]) -> Dict[str, Any]:
        """Loads or initializes the scheduler queue state from PostgreSQL."""
        record = self.db.query(ExecutionTimelineRecord).filter_by(project_id=self.project_id).first()
        if record:
            return record.scheduler_state_json

        # Initialize fresh state
        state = {
            "queue": {s_key: "waiting" for s_key in execution_order},
            "story_lookup": {s.get("story_key", "US001").upper(): s for s in stories},
            "retries": {s_key: 0 for s_key in execution_order},
            "max_retries": 3,
            "completed": [],
            "failed": []
        }
        self.save_state(state)
        return state

    def save_state(self, state: Dict[str, Any], events: List[Dict[str, Any]] = None):
        """Persists scheduler state and timeline events to PostgreSQL."""
        record = self.db.query(ExecutionTimelineRecord).filter_by(project_id=self.project_id).first()
        if not record:
            record = ExecutionTimelineRecord(project_id=self.project_id)
            self.db.add(record)
        
        record.scheduler_state_json = state
        if events:
            record.timeline_events_json = events
            
        self.db.commit()

    def execute_queue(
        self,
        stories: List[Dict[str, Any]],
        execution_order: List[str],
        dependency_graph: Dict[str, List[str]],
        run_story_fn: Callable[[Dict[str, Any]], Any]
    ) -> Dict[str, Any]:
        """Runs the scheduler queue, processing independent stories in parallel and tracking metrics in DB."""
        state = self.load_state(stories, execution_order)
        logger.info("Scheduler: Starting queue execution from PostgreSQL state: %s", state["queue"])

        events = []

        while True:
            ready_to_run = []
            for s_key, status in state["queue"].items():
                if status == "waiting":
                    deps = dependency_graph.get(s_key, [])
                    if all(dep in state["completed"] for dep in deps):
                        ready_to_run.append(s_key)

            if not ready_to_run:
                unfinished = [k for k, v in state["queue"].items() if v not in ("completed", "failed")]
                if unfinished:
                    logger.warning("Scheduler: Blocked or waiting. Unfinished: %s", unfinished)
                    for k in unfinished:
                        if state["queue"][k] == "waiting":
                            state["queue"][k] = "failed"
                            state["failed"].append(k)
                    self.save_state(state, events)
                break

            logger.info("Scheduler: Dispatching parallel execution for stories: %s", ready_to_run)

            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                future_to_story = {}
                for s_key in ready_to_run:
                    state["queue"][s_key] = "running"
                    story_payload = state["story_lookup"][s_key]
                    
                    t_start = time.time()
                    future = executor.submit(run_story_fn, story_payload)
                    future_to_story[future] = (s_key, story_payload, t_start)

                self.save_state(state, events)

                for future in as_completed(future_to_story):
                    s_key, story_payload, t_start = future_to_story[future]
                    elapsed = time.time() - t_start
                    
                    # Log Agent Execution Metrics to DB
                    metric = AgentExecutionMetric(
                        project_id=self.project_id,
                        story_key=s_key,
                        agent_name="Agent2 / Pipeline",
                        inputs_json=story_payload,
                        timings_sec=elapsed,
                        retries_count=state["retries"].get(s_key, 0)
                    )

                    try:
                        result = future.result()
                        # Success
                        state["queue"][s_key] = "completed"
                        if s_key not in state["completed"]:
                            state["completed"].append(s_key)
                        
                        metric.execution_state = "SUCCESS"
                        metric.outputs_json = result
                        
                        events.append({"timestamp": time.time(), "story_key": s_key, "event": "COMPLETED", "duration_sec": elapsed})
                        logger.info("Scheduler: Story %s completed successfully.", s_key)
                    except Exception as e:
                        # Fail and retry logic
                        logger.error("Scheduler: Story %s execution failed: %s", s_key, e)
                        retries = state["retries"].get(s_key, 0)
                        
                        metric.execution_state = "FAILED"
                        metric.outputs_json = {"error": str(e)}

                        if retries < state["max_retries"]:
                            state["retries"][s_key] = retries + 1
                            state["queue"][s_key] = "waiting"
                            events.append({"timestamp": time.time(), "story_key": s_key, "event": f"RETRY_{retries + 1}", "error": str(e)})
                        else:
                            state["queue"][s_key] = "failed"
                            if s_key not in state["failed"]:
                                state["failed"].append(s_key)
                            events.append({"timestamp": time.time(), "story_key": s_key, "event": "FAILED", "error": str(e)})

                    self.db.add(metric)
                    self.db.commit()

                self.save_state(state, events)

        return {
            "status": "COMPLETED" if not state["failed"] else "FAILED",
            "completed": state["completed"],
            "failed": state["failed"],
            "queue_state": state["queue"]
        }
