from uuid import UUID

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
