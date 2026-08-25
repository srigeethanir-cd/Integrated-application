"""Redis cache observability endpoint."""

from typing import Annotated

from fastapi import APIRouter, Depends

from app.infrastructure.redis.diagnostics import (
    RedisDiagnosticsService,
    get_redis_diagnostics_service,
)
from app.schemas.cache_statistics import CacheStatisticsResponse

router = APIRouter(tags=["cache"])
DiagnosticsDependency = Annotated[
    RedisDiagnosticsService, Depends(get_redis_diagnostics_service)
]


@router.get("/cache/statistics", response_model=CacheStatisticsResponse)
def cache_statistics(
    diagnostics: DiagnosticsDependency,
) -> CacheStatisticsResponse:
    """Return current Stage 3–6 cache statistics and Redis diagnostics."""
    return CacheStatisticsResponse.model_validate(diagnostics.collect())
