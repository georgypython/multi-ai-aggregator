from uuid import UUID
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.core.models.user_balances import UserBalance
from src.core.models.users import User
from backend.src.core.exceptions.generation import InsufficientBalanceError
from .abstract_repo import AbstractRepository


class UserRepository(AbstractRepository[User]):
    model = User

    async def get_one_with_balance(
        self,
        session: AsyncSession,
        **filters,
    ) -> User | None:
        stmt = (
            select(self.model)
            .options(
                selectinload(self.model.balance),
            )
            .filter_by(**filters)
        )
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_or_create_by_telegram_id(
        self,
        session: AsyncSession,
        available_tokens: Decimal = Decimal("0"),
        *,
        telegram_id: int,
    ) -> User:
        user = await self.get_one(
            session=session,
            telegram_id=telegram_id,
            is_active=True,
        )
        if not user:
            user = User(telegram_id=telegram_id, is_active=True)
            session.add(user)
            await session.flush()

        balance_stmt = select(UserBalance).where(UserBalance.user_id == user.id)
        balance_result = await session.execute(balance_stmt)
        balance = balance_result.scalar_one_or_none()
        if not balance:
            session.add(
                UserBalance(
                    user_id=user.id,
                    available_tokens=available_tokens,
                    hold_tokens=Decimal("0"),
                )
            )
            await session.flush()

        return user

    async def get_one_with_balance_and_llm_configuration(
        self,
        session: AsyncSession,
        **filters,
    ) -> User | None:
        stmt = (
            select(self.model)
            .options(
                selectinload(self.model.balance),
                selectinload(self.model.llm_configuration),
            )
            .filter_by(**filters)
        )
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    async def freeze_tokens(
        self,
        session: AsyncSession,
        *,
        user_id: UUID,
        amount: Decimal,
    ) -> UserBalance | None:
        if amount <= 0:
            raise ValueError("amount must be greater than 0")

        stmt = (
            select(UserBalance).where(UserBalance.user_id == user_id).with_for_update()
        )
        result = await session.execute(stmt)
        balance = result.scalar_one_or_none()

        if balance:
            if balance.available_tokens < amount:
                raise InsufficientBalanceError(
                    "amount must be less than or equal to available_tokens"
                )

            balance.available_tokens -= amount
            balance.hold_tokens += amount
            await session.flush()
            return balance

        return None

    async def get_balance_for_update(
        self,
        session: AsyncSession,
        *,
        user_id: UUID,
    ) -> UserBalance | None:
        stmt = (
            select(UserBalance).where(UserBalance.user_id == user_id).with_for_update()
        )
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    async def release_tokens(
        self,
        session: AsyncSession,
        *,
        user_id: UUID,
        amount: Decimal,
    ) -> UserBalance | None:
        if amount <= 0:
            raise ValueError("amount must be greater than 0")

        stmt = (
            select(UserBalance).where(UserBalance.user_id == user_id).with_for_update()
        )
        result = await session.execute(stmt)
        balance = result.scalar_one_or_none()

        if balance:
            release_amount = min(balance.hold_tokens, amount)
            balance.hold_tokens -= release_amount
            balance.available_tokens += release_amount
            await session.flush()
            return balance

        return None

    async def settle_hold_tokens(
        self,
        session: AsyncSession,
        *,
        user_id: UUID,
        hold_amount: Decimal,
        final_charge_amount: Decimal,
    ) -> UserBalance | None:
        if hold_amount < 0:
            raise ValueError("hold_amount must be greater or equal to 0")
        if final_charge_amount < 0:
            raise ValueError("final_charge_amount must be greater or equal to 0")

        balance = await self.get_balance_for_update(session=session, user_id=user_id)
        if not balance:
            return None

        actual_hold = min(balance.hold_tokens, hold_amount)
        balance.hold_tokens -= actual_hold
        balance.available_tokens += actual_hold

        if balance.available_tokens < final_charge_amount:
            raise InsufficientBalanceError("insufficient available_tokens for final charge")
        balance.available_tokens -= final_charge_amount

        await session.flush()
        return balance
