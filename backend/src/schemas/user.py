from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel


class UserBalanceResponseSchema(BaseModel):
    user_id: UUID
    telegram_id: int
    available_tokens: Decimal
    hold_tokens: Decimal
