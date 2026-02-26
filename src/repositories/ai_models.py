from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.core.models import AIModel

from .abstract_repo import AbstractRepository


class AIModelRepository(AbstractRepository[AIModel]):
    model = AIModel

    async def get_one_with_llm_prices(
        self,
        session: AsyncSession,
        **filters,
    ) -> AIModel | None:
        stmt = (
            select(self.model)
            .options(selectinload(self.model.llm_price))
            .filter_by(**filters)
        )
        result = await session.execute(stmt)
        return result.scalar_one_or_none()
