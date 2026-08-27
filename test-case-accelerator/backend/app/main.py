from contextlib import asynccontextmanager
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.core.config import settings, validate_llm_provider_configuration
from app.core.logging import configure_logging
from app.database.schema_validation import validate_database_schema
from app.database.session import engine
from app.infrastructure.redis import check_redis_health, close_redis_client

configure_logging()
validate_llm_provider_configuration()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI):
    try:
        validate_database_schema(engine)
    except Exception:
        logger.exception("Database schema validation failed during application startup")
        raise
    logger.info("Database schema revision validated successfully")
    redis_health = check_redis_health()
    if not redis_health.connected:
        logger.warning(
            "Redis startup validation failed: %s. Unrelated endpoints remain available.",
            redis_health.error,
        )
    try:
        yield
    finally:
        close_redis_client()

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description=(
        "Foundation API for the Test Case Accelerator platform. "
        "Domain capabilities are intentionally not implemented."
    ),
    debug=settings.debug,
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(api_router)
