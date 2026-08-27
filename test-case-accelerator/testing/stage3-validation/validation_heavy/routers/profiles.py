from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import get_db
from schemas import ProfileCreate, ProfileOut
from services.profiles import create_profile, list_profiles
router = APIRouter(prefix="/profiles")
@router.post("/", response_model=ProfileOut, status_code=201)
def create(payload: ProfileCreate, db: Session = Depends(get_db)):
    return create_profile(db, payload)
@router.get("/", response_model=list[ProfileOut])
def list_all(db: Session = Depends(get_db)):
    return list_profiles(db)
