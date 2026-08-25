from sqlalchemy import LargeBinary, String
from sqlalchemy.orm import Mapped, mapped_column
from database import Base
class StoredFile(Base):
    __tablename__ = "stored_files"
    id: Mapped[int] = mapped_column(primary_key=True)
    filename: Mapped[str] = mapped_column(String(255))
    content_type: Mapped[str] = mapped_column(String(100))
    label: Mapped[str] = mapped_column(String(80))
    size: Mapped[int] = mapped_column()
    content: Mapped[bytes] = mapped_column(LargeBinary)
