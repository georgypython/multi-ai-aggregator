from abc import ABC
from typing import Generic, TypeVar

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.base import Base

ModelT = TypeVar("ModelT", bound=Base)


class AbstractRepository(ABC, Generic[ModelT]):
    model: type[ModelT]

    async def get_one(self, session: AsyncSession, **filters) -> ModelT | None:
        stmt = select(self.model).filter_by(**filters)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_all(self, session: AsyncSession, **filters) -> list[ModelT]:
        stmt = select(self.model).filter_by(**filters)
        result = await session.execute(stmt)
        return list(result.scalars().all())
