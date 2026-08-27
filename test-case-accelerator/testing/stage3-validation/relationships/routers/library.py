from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from schemas import AuthorCreate, BookCreate, BookOut
from services.library import add_book, create_author, joined_books
router = APIRouter(prefix="/library")
@router.post("/authors", status_code=201)
def authors(payload: AuthorCreate, db: Session = Depends(get_db)):
    author = create_author(db, payload); return {"id": author.id, "name": author.name}
@router.post("/authors/{author_id}/books", response_model=BookOut, status_code=201)
def books(author_id: int, payload: BookCreate, db: Session = Depends(get_db)):
    try:
        return add_book(db, author_id, payload)
    except LookupError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
@router.get("/books", response_model=list[BookOut])
def list_books(db: Session = Depends(get_db)):
    return joined_books(db)
