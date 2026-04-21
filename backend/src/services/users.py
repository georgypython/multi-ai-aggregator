from uuid import UUID
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.models import User, UserBalance
from src.schemas import UserBalanceResponseSchema
from src.services.db_access import DBAccessService


class UsersService(DBAccessService):
    def __init__(self, session: AsyncSession, new_user_free_tokens: int) -> None:
        self.new_user_free_tokens = Decimal(new_user_free_tokens)
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

    async def get_active_user(self, user_id: UUID) -> User:
        stmt = select(User).where(
            User.id == user_id,
            User.is_active.is_(True),
            User.is_whitelist.is_(True),
        )
        result = await self.session.execute(stmt)
        user = result.scalar_one_or_none()
        if not user:
            raise ValueError(f"Active user not found for user_id={user_id}")
        return user

    async def get_active_user_by_tg_id_with_creation(self, telegram_id: int) -> User:
        async with self.session.begin():
            stmt = select(User).where(
                User.telegram_id == telegram_id,
                User.is_active.is_(True),
            )

            result = await self.session.execute(stmt)
            user = result.scalar_one_or_none()

            if not user:
                user = User(telegram_id=telegram_id, is_active=True)
                self.session.add(user)
                await self.session.flush()

            balance_stmt = select(UserBalance).where(UserBalance.user_id == user.id)
            balance_result = await self.session.execute(balance_stmt)
            balance = balance_result.scalar_one_or_none()
            if not balance:
                self.session.add(
                    UserBalance(
                        user_id=user.id,
                        available_tokens=self.new_user_free_tokens,
                        hold_tokens=Decimal("0"),
                    )
                )
                await self.session.flush()
        return user
