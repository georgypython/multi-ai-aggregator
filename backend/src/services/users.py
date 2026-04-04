from uuid import UUID
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.models import User
from src.schemas import UserBalanceResponseSchema
from src.services.db_access import DBAccessService


class UsersService(DBAccessService):
    def __init__(
        self,
        session: AsyncSession,
    ) -> None:
        self.session = session

    async def _get_user_with_balance(self, **filters) -> User | None:
        stmt = select(User).options(selectinload(User.balance)).filter_by(**filters)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_user_balance(
        self,
        user_id: UUID,
    ) -> UserBalanceResponseSchema:
        user = await self._get_user_with_balance(
            id=user_id,
            is_active=True,
        )
        if not user:
            raise ValueError(f"Active user not found for user_id={user_id}")
        available_tokens = (
            user.balance.available_tokens if user.balance else Decimal("0")
        )
        hold_tokens = user.balance.hold_tokens if user.balance else Decimal("0")

        return UserBalanceResponseSchema(
            user_id=user.id,
            telegram_id=user.telegram_id,
            available_tokens=available_tokens,
            hold_tokens=hold_tokens,
        )
