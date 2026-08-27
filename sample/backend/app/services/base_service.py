"""Generic base service class providing common business logic lifecycle methods."""

from typing import Any, Dict, Generic, List, Optional, TypeVar, Union

from app.core.exceptions import NotFoundError
from app.database.repository_base import BaseRepository, ModelType

RepositoryType = TypeVar("RepositoryType", bound=BaseRepository)


class BaseService(Generic[ModelType, RepositoryType]):
    """Generic service layer encapsulating business logic over generic repositories."""

    def __init__(self, repository: RepositoryType):
        self.repository = repository

    def get_by_id(self, id: Any, raise_if_missing: bool = True) -> Optional[ModelType]:
        """Fetch a record by primary key with optional NotFoundError raising."""
        item = self.repository.get(id)
        if not item and raise_if_missing:
            raise NotFoundError(resource=self.repository.model.__name__, identifier=id)
        return item

    def list(self, skip: int = 0, limit: int = 100) -> List[ModelType]:
        """Fetch a list of records with pagination."""
        return self.repository.get_all(skip=skip, limit=limit)

    def filter_by(self, skip: int = 0, limit: int = 100, **kwargs: Any) -> List[ModelType]:
        """Fetch records matching exact field values."""
        return self.repository.filter_by(skip=skip, limit=limit, **kwargs)

    def count(self, **kwargs: Any) -> int:
        """Count total matching records."""
        return self.repository.count(**kwargs)

    def create(self, obj_in: Union[Dict[str, Any], Any]) -> ModelType:
        """Create a new record."""
        return self.repository.create(obj_in)

    def update(self, id: Any, obj_in: Union[Dict[str, Any], Any]) -> ModelType:
        """Update an existing record by primary key."""
        item = self.get_by_id(id, raise_if_missing=True)
        return self.repository.update(item, obj_in)

    def delete(self, id: Any) -> bool:
        """Delete a record by primary key."""
        self.get_by_id(id, raise_if_missing=True)
        return self.repository.delete(id)
