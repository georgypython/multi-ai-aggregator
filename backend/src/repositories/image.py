from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .abstract_repo import AbstractRepository

from src.core.models import ImageProfile, ImagePrice


class ImageProfileRepository(AbstractRepository[ImageProfile]):
    model = ImageProfile


class ImagePriceRepository(AbstractRepository[ImagePrice]):
    model = ImagePrice

    async def get_one_by_ai_model_size_quality(
        self,
        session: AsyncSession,
        *,
        ai_model_id: UUID,
        size: str,
        quality: str,
    ) -> ImagePrice | None:
        stmt = (
            select(self.model)
            .join(ImageProfile, self.model.image_profile_id == ImageProfile.id)
            .where(
                ImageProfile.ai_model_id == ai_model_id,
                self.model.size == size,
                self.model.quality == quality,
            )
        )
        result = await session.execute(stmt)
        return result.scalar_one_or_none()



