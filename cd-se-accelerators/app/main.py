"""
Application entry-point.

Configures logging, creates the FastAPI application, and registers all
routers.  Run with::

    uvicorn app.main:app --reload
"""

import logging
import sys

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.source_routes import router as source_router
from app.api.framework_routes import router as framework_router
from app.api.analyzer_routes import router as analyzer_router
from app.api.frontend_context_routes import router as frontend_context_router
from app.api.behavior_inventory_routes import router as behavior_inventory_router
from app.api.ir_routes import router as ir_router
from app.api.strategy_routes import router as strategy_router
from app.api.edge_case_routes import router as edge_case_router
from app.api.test_case_routes import router as test_case_router
from app.api.test_writer_routes import router as test_writer_router
from app.api.test_execution_routes import router as test_execution_router
from app.api.validation_routes import router as validation_router
from app.api.pipeline_routes import router as pipeline_router
from app.api.test_case_storage_routes import router as test_case_storage_router
from app.api.project_routes import router as project_router

from app.db.database import init_db

# ---------------------------------------------------------------------------
# Logging configuration
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[logging.StreamHandler(sys.stdout)],
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# FastAPI application
# ---------------------------------------------------------------------------
app = FastAPI(
    title="AI Frontend Unit Test Generator",
    description=(
        "Framework-agnostic AI-powered tool for generating frontend unit "
        "tests.  Supports source ingestion, framework detection, "
        "project analysis, IR generation, and test strategy generation."
    ),
    version="0.1.0",
)

# Enable CORS for local development and frontend app
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:8000",
    ],
    allow_origin_regex=r"http://(localhost|127\.0\.0\.1)(:[0-9]+)?",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(source_router)
app.include_router(framework_router)
app.include_router(analyzer_router)
app.include_router(frontend_context_router)
app.include_router(behavior_inventory_router)
app.include_router(ir_router)
app.include_router(strategy_router)
app.include_router(edge_case_router)
app.include_router(test_case_router)
app.include_router(test_writer_router)
app.include_router(test_execution_router)
app.include_router(validation_router)
app.include_router(pipeline_router)
app.include_router(test_case_storage_router)
app.include_router(project_router)


@app.on_event("startup")
def on_startup():
    """Initialize database tables on application startup and seed initial mock projects."""
    init_db()
    try:
        from app.db.seed import seed_initial_mock_projects
        from app.db.database import SessionLocal
        db = SessionLocal()
        try:
            seed_initial_mock_projects(db)
        finally:
            db.close()
    except Exception as exc:
        logger.error("Error during startup database seeding: %s", exc)


@app.get("/", tags=["Health"])
async def health_check() -> dict:
    """Simple liveness probe."""
    return {"status": "ok", "version": app.version}


logger.info("Application started – registered API routes:")
for path, operations in app.openapi()["paths"].items():
    for method in operations:
        logger.info("  %s %s", method.upper(), path)
