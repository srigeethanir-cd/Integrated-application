from fastapi import APIRouter, Query
from .filter_service import filter_tasks_by_status

router = APIRouter(prefix="/api/v1/tasks", tags=["Filter"])

@router.get("/filter")
def filter_tasks(status: str = Query("All", description="Filter status")):
    return filter_tasks_by_status(status)
