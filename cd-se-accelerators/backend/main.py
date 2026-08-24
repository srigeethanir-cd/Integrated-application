"""Application entry point for the CD-SE Accelerators backend."""

import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles

from app.api.router import api_router
from app.core.config import get_settings
from app.core.exceptions import register_exception_handlers
from app.middleware import register_middlewares
from app.database.session import Base, engine
import app.models

settings = get_settings()


@asynccontextmanager
async def lifespan(_: FastAPI):
    """Initialize local development storage before serving requests."""
    Base.metadata.create_all(bind=engine)
    # Check if we need to add columns to user_stories table dynamically (e.g. for Postgres)
    from sqlalchemy import text
    statements = [
        "ALTER TABLE user_stories ADD COLUMN IF NOT EXISTS generation_status VARCHAR(50) DEFAULT 'DRAFT';",
        "ALTER TABLE user_stories ADD COLUMN IF NOT EXISTS validation_status VARCHAR(50) DEFAULT 'PENDING';",
        "ALTER TABLE user_stories ADD COLUMN IF NOT EXISTS preview_status VARCHAR(50) DEFAULT 'PENDING';",
        "ALTER TABLE user_stories ADD COLUMN IF NOT EXISTS merge_status VARCHAR(50) DEFAULT 'PENDING';",
        "ALTER TABLE user_stories ADD COLUMN IF NOT EXISTS export_status VARCHAR(50) DEFAULT 'PENDING';",
        "ALTER TABLE user_stories ADD COLUMN IF NOT EXISTS version VARCHAR(20) DEFAULT '1.0';",
        "ALTER TABLE user_stories ADD COLUMN IF NOT EXISTS retry_count INTEGER DEFAULT 0;",
        "ALTER TABLE user_stories ADD COLUMN IF NOT EXISTS assigned_agent VARCHAR(50) DEFAULT 'Agent2';",
        "ALTER TABLE user_stories ADD COLUMN IF NOT EXISTS execution_timestamp TIMESTAMP WITH TIME ZONE;",
        "ALTER TABLE user_stories ADD COLUMN IF NOT EXISTS audit_trail JSONB;",
        "ALTER TABLE prompt_approvals ADD COLUMN IF NOT EXISTS bundle_json JSON;",
        "ALTER TABLE projects ADD COLUMN IF NOT EXISTS requirements_json JSON;",
        "ALTER TABLE blueprints ADD COLUMN IF NOT EXISTS user_story_id VARCHAR(50);",
        "ALTER TABLE blueprints ADD COLUMN IF NOT EXISTS epic_id VARCHAR(50);",
        "ALTER TABLE blueprints ADD COLUMN IF NOT EXISTS file_name VARCHAR(255);",
        "ALTER TABLE blueprints ADD COLUMN IF NOT EXISTS file_path TEXT;",
        "ALTER TABLE blueprints ADD COLUMN IF NOT EXISTS artifact_type VARCHAR(50);"
    ]
    for stmt in statements:
        try:
            with engine.begin() as conn:
                conn.execute(text(stmt))
        except Exception:
            pass
    yield


def create_application() -> FastAPI:
    app = FastAPI(title=settings.app_name, version=settings.api_version, lifespan=lifespan)
    register_middlewares(app)
    register_exception_handlers(app)
    app.include_router(api_router, prefix=settings.api_prefix)

    # Mount UI Dashboard router for story explorer & workspace endpoints
    try:
        from ui_dashboard.router import router as ui_dashboard_router, workspace_router
        app.include_router(ui_dashboard_router)
        app.include_router(workspace_router)
    except Exception as e:
        print(f"Warning: Could not import ui_dashboard router: {e}")

    # Mount static dashboard UI folder
    static_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "app", "static")
    if os.path.exists(static_dir):
        app.mount("/ui", StaticFiles(directory=static_dir, html=True), name="static")

    return app


app = create_application()


@app.get("/", include_in_schema=False)
def root() -> RedirectResponse:
    """Send the local development root URL to Swagger UI."""
    return RedirectResponse(url="/docs")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=True,
        reload_dirs=["app", "agents", "ui_dashboard"]
    )

