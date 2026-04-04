from typing import TypeVar

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.base import Base

ModelT = TypeVar("ModelT", bound=Base)


class DBAccessService:
    session: AsyncSession

    async def get_one(self, *, model: type[ModelT], **filters) -> ModelT | None:
        stmt = select(model).filter_by(**filters)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_all(self, *, model: type[ModelT], **filters) -> list[ModelT]:
        stmt = select(model).filter_by(**filters)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
