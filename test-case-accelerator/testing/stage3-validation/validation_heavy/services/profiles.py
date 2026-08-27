from sqlalchemy import select
from sqlalchemy.orm import Session
from models import Profile
from schemas import ProfileCreate
def create_profile(db: Session, payload: ProfileCreate) -> Profile:
    profile = Profile(username=payload.username, email=payload.email, age=payload.age, tags=payload.tags)
    db.add(profile); db.commit(); db.refresh(profile); return profile
def list_profiles(db: Session) -> list[Profile]:
    return list(db.scalars(select(Profile).order_by(Profile.username)))
