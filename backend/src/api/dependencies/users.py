from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends

from .session import get_session
from src.services.users import UsersService
from src.core.config import settings


async def get_users_service(
    session: AsyncSession = Depends(get_session),
) -> UsersService:
    return UsersService(
        session=session, new_user_free_tokens=settings.ai_logic.new_user_free_tokens
    )
