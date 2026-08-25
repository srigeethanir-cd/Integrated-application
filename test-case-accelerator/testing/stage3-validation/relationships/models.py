from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from database import Base

class Author(Base):
    __tablename__ = "authors"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), index=True)
    books: Mapped[list["Book"]] = relationship(back_populates="author", cascade="all, delete-orphan")

class Publisher(Base):
    __tablename__ = "publishers"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True)
    books: Mapped[list["Book"]] = relationship(back_populates="publisher")

class Book(Base):
    __tablename__ = "books"
    __table_args__ = (UniqueConstraint("publisher_id", "isbn"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(200))
    isbn: Mapped[str] = mapped_column(String(20), index=True)
    author_id: Mapped[int] = mapped_column(ForeignKey("authors.id", ondelete="CASCADE"))
    publisher_id: Mapped[int] = mapped_column(ForeignKey("publishers.id"))
    author: Mapped[Author] = relationship(back_populates="books")
    publisher: Mapped[Publisher] = relationship(back_populates="books")
