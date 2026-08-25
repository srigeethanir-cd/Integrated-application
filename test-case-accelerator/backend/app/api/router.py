from fastapi import APIRouter

from app.api.v1.endpoints.health import router as health_router
from app.api.v1.endpoints.dependencies import router as dependencies_router
from app.api.v1.endpoints.code_understanding import (
    router as code_understanding_router,
)
from app.api.v1.endpoints.projects import router as projects_router
from app.api.v1.endpoints.workflows import router as workflows_router
from app.api.v1.endpoints.runtime_validation import router as runtime_validation_router
from app.api.v1.endpoints.cache_statistics import router as cache_statistics_router
from app.api.v1.endpoints.security_scans import router as security_scans_router
from app.api.v1.endpoints.exports import router as exports_router

api_router = APIRouter()
api_router.include_router(health_router)
api_router.include_router(projects_router)
api_router.include_router(dependencies_router)
api_router.include_router(code_understanding_router)
api_router.include_router(workflows_router)
api_router.include_router(runtime_validation_router)
api_router.include_router(cache_statistics_router)
api_router.include_router(security_scans_router)
api_router.include_router(exports_router)
