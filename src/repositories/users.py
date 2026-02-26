from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.core.models.users import User

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
