from uuid import UUID
from decimal import Decimal

from fastapi import Depends, HTTPException, Query, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import settings
from src.models import User, UserBalance

from .session import get_session

bearer_scheme = HTTPBearer(auto_error=False)


async def require_api_key(
    credentials: HTTPAuthorizationCredentials | None = Security(bearer_scheme),
) -> None:
    expected_api_key = settings.api.api_key
    if not expected_api_key or expected_api_key == "YOUR_API_KEY":
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Server API key is not configured",
        )

    api_key = credentials.credentials if credentials else None
    if api_key != expected_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
        )


async def resolve_user_id_by_telegram_id(
    tg_user_id: int = Query(..., ge=1),
    session: AsyncSession = Depends(get_session),
) -> UUID:
    async with session.begin():
        stmt = select(User).where(
            User.telegram_id == tg_user_id, User.is_active.is_(True)
        )
        result = await session.execute(stmt)
        user = result.scalar_one_or_none()

        if not user:
            user = User(telegram_id=tg_user_id, is_active=True)
            session.add(user)
            await session.flush()

        balance_stmt = select(UserBalance).where(UserBalance.user_id == user.id)
        balance_result = await session.execute(balance_stmt)
        balance = balance_result.scalar_one_or_none()
        if not balance:
            session.add(
                UserBalance(
                    user_id=user.id,
                    available_tokens=settings.ai_logic.new_user_free_tokens,
                    hold_tokens=Decimal("0"),
                )
            )
            await session.flush()
        return user.id
