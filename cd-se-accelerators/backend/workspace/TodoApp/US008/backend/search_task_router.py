from fastapi import APIRouter, Query
from .search_service import search_tasks_by_query

router = APIRouter(prefix="/api/v1/tasks", tags=["Search"])

@router.get("/search")
def search_tasks(q: str = Query("", description="Search term")):
    return search_tasks_by_query(q)
