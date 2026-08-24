from fastapi import APIRouter
from .dashboard_service import get_dashboard_summary

router = APIRouter(prefix="/api/v1/dashboard", tags=["Dashboard"])

@router.get("/summary")
def dashboard_summary():
    return get_dashboard_summary()
