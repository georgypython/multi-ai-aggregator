from uuid import UUID
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from src.core.schemas.ai import UserBalanceResponseSchema
from src.repositories import UserRepository


class UsersService:
    def __init__(
        self,
        session: AsyncSession,
        user_repo: UserRepository,
    ) -> None:
        self.session = session
        self.user_repo = user_repo

    async def get_user_balance(
        self,
        user_id: str,
    ) -> UserBalanceResponseSchema:
        parsed_uuid: UUID | None = None
        try:
            parsed_uuid = UUID(user_id)
        except ValueError:
            parsed_uuid = None

        async with self.session.begin():
            if parsed_uuid is not None:
                user = await self.user_repo.get_one_with_balance(
                    session=self.session,
                    id=parsed_uuid,
                    is_active=True,
                )
            elif user_id.isdigit():
                user = await self.user_repo.get_one_with_balance(
                    session=self.session,
                    telegram_id=int(user_id),
                    is_active=True,
                )
            else:
                raise ValueError("Invalid user_id format")

            if not user:
                raise ValueError(f"Active user not found for user_id={user_id}")

            available_tokens = user.balance.available_tokens if user.balance else Decimal("0")
            hold_tokens = user.balance.hold_tokens if user.balance else Decimal("0")

            return UserBalanceResponseSchema(
                user_id=user.id,
                telegram_id=user.telegram_id,
                available_tokens=available_tokens,
                hold_tokens=hold_tokens,
            )
