from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column
from database import Base
class Job(Base):
    __tablename__ = "jobs"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    state: Mapped[str] = mapped_column(String(20), default="new")
