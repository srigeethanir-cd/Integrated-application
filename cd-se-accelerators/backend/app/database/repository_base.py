"""Generic repository base class implementing standard CRUD operations."""

from typing import Any, Dict, Generic, List, Optional, Type, TypeVar, Union

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.database.base import Base

ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    """Generic repository providing standardized database operations for ORM models."""

    def __init__(self, model: Type[ModelType], db: Session):
        self.model = model
        self.db = db

    def get(self, id: Any) -> Optional[ModelType]:
        """Fetch a single record by primary key."""
        return self.db.get(self.model, id)

    def get_all(self, skip: int = 0, limit: int = 100) -> List[ModelType]:
        """Fetch multiple records with pagination."""
        stmt = select(self.model).offset(skip).limit(limit)
        return list(self.db.scalars(stmt).all())

    def filter_by(self, skip: int = 0, limit: int = 100, **kwargs: Any) -> List[ModelType]:
        """Fetch records filtered by exact attribute matches."""
        stmt = select(self.model).filter_by(**kwargs).offset(skip).limit(limit)
        return list(self.db.scalars(stmt).all())

    def find_one(self, **kwargs: Any) -> Optional[ModelType]:
        """Fetch the first record matching filter criteria."""
        stmt = select(self.model).filter_by(**kwargs)
        return self.db.scalars(stmt).first()

    def create(self, obj_in: Union[Dict[str, Any], ModelType]) -> ModelType:
        """Create and persist a new record."""
        if isinstance(obj_in, dict):
            db_obj = self.model(**obj_in)
        else:
            db_obj = obj_in
        self.db.add(db_obj)
        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj

    def bulk_create(self, objs: List[Union[Dict[str, Any], ModelType]]) -> List[ModelType]:
        """Persist multiple records in a batch."""
        db_objs = [
            self.model(**obj) if isinstance(obj, dict) else obj
            for obj in objs
        ]
        self.db.add_all(db_objs)
        self.db.commit()
        for obj in db_objs:
            self.db.refresh(obj)
        return db_objs

    def update(
        self, db_obj: ModelType, obj_in: Union[Dict[str, Any], ModelType]
    ) -> ModelType:
        """Update an existing record."""
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.to_dict() if hasattr(obj_in, "to_dict") else obj_in.__dict__

        # pyrefly: ignore [missing-attribute]
        for field, value in update_data.items():
            if hasattr(db_obj, field) and field != "id":
                setattr(db_obj, field, value)

        self.db.add(db_obj)
        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj

    def delete(self, id: Any) -> bool:
        """Delete a record by primary key."""
        obj = self.get(id)
        if obj:
            self.db.delete(obj)
            self.db.commit()
            return True
        return False

    def count(self, **kwargs: Any) -> int:
        """Count total records matching filter criteria."""
        stmt = select(func.count()).select_from(self.model)
        if kwargs:
            stmt = stmt.filter_by(**kwargs)
        return self.db.scalar(stmt) or 0

    def exists(self, id: Any) -> bool:
        """Check if a record exists by primary key."""
        return self.get(id) is not None
