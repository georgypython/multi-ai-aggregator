from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .abstract_repo import AbstractRepository

from src.models import VideoProfile, VideoPrice


class VideoProfileRepository(AbstractRepository[VideoProfile]):
    model = VideoProfile


class VideoPriceRepository(AbstractRepository[VideoPrice]):
    model = VideoPrice

    async def get_one_by_ai_model_duration_size(
        self,
        session: AsyncSession,
        *,
        ai_model_id: UUID,
        duration_seconds: int,
        size: str,
    ) -> VideoPrice | None:
        stmt = (
            select(self.model)
            .join(VideoProfile, self.model.video_profile_id == VideoProfile.id)
            .where(
                VideoProfile.ai_model_id == ai_model_id,
                self.model.duration_seconds == duration_seconds,
                self.model.size == size,
            )
        )
        result = await session.execute(stmt)
        return result.scalar_one_or_none()
