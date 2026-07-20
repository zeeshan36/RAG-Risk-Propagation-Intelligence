"""In-memory repository for minimal-mode storage."""
from typing import Callable, Dict, List, Type, TypeVar

from pydantic import BaseModel

from common.exceptions import RepositoryError

T = TypeVar("T", bound=BaseModel)


class SimpleRepository:
    """Thread-unsafe in-memory store keyed by model class name."""

    def __init__(self) -> None:
        self._store: Dict[str, Dict[str, BaseModel]] = {}

    @staticmethod
    def _key(model_cls: Type[BaseModel]) -> str:
        return model_cls.__name__

    def upsert(self, entity: BaseModel) -> None:
        """Insert or replace a single entity."""
        key = self._key(type(entity))
        self._store.setdefault(key, {})[entity.id] = entity

    def load_many(self, entities: List[BaseModel]) -> int:
        """Bulk upsert and return count."""
        for entity in entities:
            self.upsert(entity)
        return len(entities)

    def get(self, model_cls: Type[T], entity_id: str) -> T:
        """Retrieve a single entity by ID."""
        key = self._key(model_cls)
        try:
            return self._store[key][entity_id]  # type: ignore[return-value]
        except KeyError as exc:
            raise RepositoryError(
                f"{model_cls.__name__} with id={entity_id} not found"
            ) from exc

    def list(self, model_cls: Type[T]) -> List[T]:
        """Return all stored entities of a given type."""
        key = self._key(model_cls)
        return list(self._store.get(key, {}).values())  # type: ignore[arg-type]

    def find(
        self,
        model_cls: Type[T],
        predicate: Callable[[T], bool],
    ) -> List[T]:
        """Return entities matching predicate."""
        return [e for e in self.list(model_cls) if predicate(e)]

    def delete(self, model_cls: Type[T], entity_id: str) -> bool:
        """Delete entity by ID. Returns True if it existed."""
        key = self._key(model_cls)
        if key not in self._store:
            return False
        return self._store[key].pop(entity_id, None) is not None

    def count(self, model_cls: Type[T]) -> int:
        """Return number of stored entities of a given type."""
        key = self._key(model_cls)
        return len(self._store.get(key, {}))

    def type_count(self) -> int:
        """Return number of distinct entity types stored."""
        return len(self._store)

    def total_count(self) -> int:
        """Return total number of stored entities across all types."""
        return sum(len(bucket) for bucket in self._store.values())

    def clear(self) -> None:
        """Remove all stored entities."""
        self._store.clear()
