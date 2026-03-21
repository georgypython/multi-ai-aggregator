from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.models import AIModel, ImageProfile, LLMProfile, VideoProfile
from src.models.enums import ModelType

from .abstract_repo import AbstractRepository


class AIModelRepository(AbstractRepository[AIModel]):
    model = AIModel

    async def get_one_with_profile(
        self,
        session: AsyncSession,
        *,
        ai_model_id: UUID,
        model_type: ModelType,
    ) -> AIModel | None:
        stmt = select(self.model).where(self.model.id == ai_model_id)

        if model_type == ModelType.IMAGE:
            stmt = stmt.options(selectinload(self.model.image_profile))
        elif model_type == ModelType.VIDEO:
            stmt = stmt.options(selectinload(self.model.video_profile))
        elif model_type == ModelType.LLM:
            stmt = stmt.options(selectinload(self.model.llm_profile))
        else:
            raise ValueError(f"Unsupported model_type={model_type}")

        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_one_with_image_profile_and_prices(
        self,
        session: AsyncSession,
        *,
        ai_model_id: UUID,
    ) -> AIModel | None:
        return await self.get_one_with_profile(
            session=session,
            ai_model_id=ai_model_id,
            model_type=ModelType.IMAGE,
        )

    async def get_one_with_video_profile_and_prices(
        self,
        session: AsyncSession,
        *,
        ai_model_id: UUID,
    ) -> AIModel | None:
        return await self.get_one_with_profile(
            session=session,
            ai_model_id=ai_model_id,
            model_type=ModelType.VIDEO,
        )
