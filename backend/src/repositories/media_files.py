from sqlalchemy.ext.asyncio import AsyncSession

from src.core.models import MediaFile
from .abstract_repo import AbstractRepository


class MediaFilesRepository(AbstractRepository[MediaFile]):
    model = MediaFile

    async def add_uploaded_items(
        self,
        session: AsyncSession,
        items: list[dict],
    ) -> list[MediaFile]:
        media_files = [
            MediaFile(**item) for item in items
        ]
        session.add_all(media_files)
        await session.flush()
        return media_files

