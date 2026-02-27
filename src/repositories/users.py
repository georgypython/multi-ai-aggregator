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

    async def get_one_with_balance(
        self,
        session: AsyncSession,
        **filters,
    ) -> User | None:
        stmt = (
            select(self.model)
            .options(selectinload(self.model.balance))
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
