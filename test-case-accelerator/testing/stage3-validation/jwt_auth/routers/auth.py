from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from database import get_db
from models import User
from schemas import RefreshRequest, RegisterRequest, TokenPair, UserOut
from services.auth import InvalidCredentialsError, InvalidTokenError, authenticate, decode_token, issue_pair, register, rotate_refresh

router = APIRouter(prefix="/auth", tags=["auth"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    try:
        payload = decode_token(token, "access")
        user = db.get(User, int(payload["sub"]))
        if user is None:
            raise InvalidTokenError("user not found")
        return user
    except InvalidTokenError as error:
        raise HTTPException(status_code=401, detail=str(error), headers={"WWW-Authenticate": "Bearer"}) from error

def require_admin(user: User = Depends(get_current_user)) -> User:
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="admin role required")
    return user

@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def create_user(payload: RegisterRequest, db: Session = Depends(get_db)):
    try:
        return register(db, payload)
    except ValueError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error

@router.post("/login", response_model=TokenPair)
def login(form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    try:
        access, refresh = issue_pair(db, authenticate(db, form.username, form.password))
        return TokenPair(access_token=access, refresh_token=refresh)
    except InvalidCredentialsError as error:
        raise HTTPException(status_code=401, detail=str(error)) from error

@router.post("/refresh", response_model=TokenPair)
def refresh(payload: RefreshRequest, db: Session = Depends(get_db)):
    try:
        access, refresh_token = rotate_refresh(db, payload.refresh_token)
        return TokenPair(access_token=access, refresh_token=refresh_token)
    except InvalidTokenError as error:
        raise HTTPException(status_code=401, detail=str(error)) from error

@router.get("/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)):
    return user

@router.get("/admin", response_model=UserOut)
def admin(user: User = Depends(require_admin)):
    return user
