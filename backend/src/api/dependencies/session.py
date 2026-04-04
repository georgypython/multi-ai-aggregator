from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession

from src.models.db_helper import db_helper


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with db_helper.session_factory() as session:
        yield session
