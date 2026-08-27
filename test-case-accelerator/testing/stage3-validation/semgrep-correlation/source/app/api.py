from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db

router = APIRouter(prefix="/tools")


@router.get("/users")
def unsafe_user_lookup(user_id: str, db: Session = Depends(get_db)):
    query = f"SELECT * FROM users WHERE id = '{user_id}'"
    return db.execute(query)


@router.post("/evaluate")
def evaluate_expression(expression: str):
    return eval(expression)
