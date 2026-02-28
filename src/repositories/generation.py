from uuid import UUID
from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.models.enums import GenerationStatus
from .abstract_repo import AbstractRepository


from src.core.models import AIGeneration


class GenerationRepository(AbstractRepository[AIGeneration]):
    model = AIGeneration

    async def create_processing(
        self,
        session: AsyncSession,
        *,
        user_id: UUID,
        ai_model_id: UUID,
    ) -> AIGeneration:
        generation = AIGeneration(
            user_id=user_id,
            ai_model_id=ai_model_id,
            status=GenerationStatus.PROCESSING,
            charged_tokens=0.0,
        )
        session.add(generation)
        await session.flush()
        return generation

    async def mark_failed(
        self,
        session: AsyncSession,
        *,
        generation_id: UUID,
    ) -> AIGeneration | None:
        generation = await session.get(AIGeneration, generation_id)
        if not generation:
            return None

        generation.status = GenerationStatus.FAILED
        await session.flush()
        return generation

    async def mark_completed(
        self,
        session: AsyncSession,
        *,
        generation_id: UUID,
        charged_tokens: float,
    ) -> AIGeneration | None:
        generation = await session.get(AIGeneration, generation_id)
        if not generation:
            return None

        generation.status = GenerationStatus.COMPLETED
        generation.charged_tokens = charged_tokens
        generation.completed_at = datetime.now(timezone.utc)
        await session.flush()
        return generation

    async def count_by_user_and_model(
        self,
        session: AsyncSession,
        *,
        user_id: UUID,
        ai_model_id: UUID,
        max_count: int | None = None,
    ) -> int:
        base_stmt = select(self.model.id).where(
            self.model.user_id == user_id,
            self.model.ai_model_id == ai_model_id,
        )
        if max_count is not None and max_count > 0:
            base_stmt = base_stmt.limit(max_count)

        stmt = select(func.count()).select_from(base_stmt.subquery())
        result = await session.execute(stmt)
        return int(result.scalar_one() or 0)
