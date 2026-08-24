from fastapi import APIRouter
from .logout_service import revoke_session

router = APIRouter(prefix="/api/v1/auth", tags=["Authentication"])

@router.post("/logout")
def logout():
    return revoke_session()
