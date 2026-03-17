from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.models import MediaFile
from .abstract_repo import AbstractRepository


class MediaFilesRepository(AbstractRepository[MediaFile]):
    model = MediaFile

    async def add_uploaded_items(
        self,
        session: AsyncSession,
        items: list[dict[str, Any]],
    ) -> list[MediaFile]:
        media_files = [
            MediaFile(**item) for item in items
        ]
        session.add_all(media_files)
        await session.flush()
        return media_files

    async def get_active_user_files_by_ids(
        self,
        session: AsyncSession,
        user_id: UUID,
        media_file_ids: list[UUID],
        now: datetime,
    ) -> list[MediaFile]:
        if not media_file_ids:
            return []

        stmt = select(self.model).where(
            self.model.user_id == user_id,
            self.model.id.in_(media_file_ids),
            self.model.expires_at > now,
        )
        result = await session.execute(stmt)
        return list(result.scalars().all())

