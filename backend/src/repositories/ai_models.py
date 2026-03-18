from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.core.models import AIModel, ImageProfile, VideoProfile

from .abstract_repo import AbstractRepository


class AIModelRepository(AbstractRepository[AIModel]):
    model = AIModel

    async def get_one_with_image_profile_and_prices(
        self,
        session: AsyncSession,
        *,
        ai_model_id: UUID,
    ) -> AIModel | None:
        stmt = (
            select(self.model)
            .options(
                selectinload(self.model.image_profile).selectinload(ImageProfile.prices),
            )
            .where(self.model.id == ai_model_id)
        )
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_one_with_video_profile_and_prices(
        self,
        session: AsyncSession,
        *,
        ai_model_id: UUID,
    ) -> AIModel | None:
        stmt = (
            select(self.model)
            .options(
                selectinload(self.model.video_profile).selectinload(VideoProfile.prices),
            )
            .where(self.model.id == ai_model_id)
        )
        result = await session.execute(stmt)
        return result.scalar_one_or_none()
