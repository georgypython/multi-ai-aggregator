from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.models import LLMProfile

from .abstract_repo import AbstractRepository


class LLMProfileRepository(AbstractRepository[LLMProfile]):
    model = LLMProfile

    async def get_one_with_ai_model(
        self,
        session: AsyncSession,
        *,
        ai_model_id: UUID,
    ) -> LLMProfile | None:
        stmt = (
            select(self.model)
            .options(
                selectinload(self.model.ai_model),
            )
            .where(self.model.ai_model_id == ai_model_id)
        )
        result = await session.execute(stmt)
        return result.scalar_one_or_none()
