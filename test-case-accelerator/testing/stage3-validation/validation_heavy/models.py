from sqlalchemy import JSON, String
from sqlalchemy.orm import Mapped, mapped_column
from database import Base
class Profile(Base):
    __tablename__ = "profiles"
    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(24), unique=True, index=True)
    email: Mapped[str] = mapped_column(String(200))
    age: Mapped[int] = mapped_column()
    tags: Mapped[list[str]] = mapped_column(JSON, default=list)
