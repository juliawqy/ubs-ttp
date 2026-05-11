"""Base repository class — all DB repositories inherit from this."""
from abc import ABC, abstractmethod
from typing import Generic, TypeVar

ModelType = TypeVar("ModelType")


class BaseRepository(ABC, Generic[ModelType]):
    """
    Abstract base repository.
    Concrete repositories implement these methods for their specific model.
    Keeps DB access logic out of service classes (SRP).
    """

    @abstractmethod
    async def get_by_id(self, id: int) -> ModelType | None:
        raise NotImplementedError

    @abstractmethod
    async def get_all(self) -> list[ModelType]:
        raise NotImplementedError

    @abstractmethod
    async def create(self, data: dict) -> ModelType:
        raise NotImplementedError

    @abstractmethod
    async def update(self, id: int, data: dict) -> ModelType | None:
        raise NotImplementedError

    @abstractmethod
    async def delete(self, id: int) -> bool:
        raise NotImplementedError
