from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.core.models.user_balances import UserBalance
from src.core.models.users import User
from src.core.exceptions.llm import InsufficientBalanceError
from .abstract_repo import AbstractRepository


class UserRepository(AbstractRepository[User]):
    model = User

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
        amount: float,
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
                    "amount must be letter than available_tokens"
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
        amount: float,
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
        hold_amount: float,
        final_charge_amount: float,
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
