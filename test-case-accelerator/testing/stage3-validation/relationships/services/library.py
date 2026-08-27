from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload
from models import Author, Book, Publisher
from schemas import AuthorCreate, BookCreate
def create_author(db: Session, payload: AuthorCreate) -> Author:
    author = Author(name=payload.name); db.add(author); db.commit(); db.refresh(author); return author
def add_book(db: Session, author_id: int, payload: BookCreate) -> Book:
    author = db.get(Author, author_id)
    if author is None:
        raise LookupError("author not found")
    publisher = db.scalar(select(Publisher).where(Publisher.name == payload.publisher_name))
    if publisher is None:
        publisher = Publisher(name=payload.publisher_name)
    book = Book(title=payload.title, isbn=payload.isbn, author=author, publisher=publisher)
    db.add(book); db.commit(); db.refresh(book); return book
def joined_books(db: Session) -> list[Book]:
    statement = select(Book).options(joinedload(Book.author), joinedload(Book.publisher))
    return list(db.scalars(statement))
