from typing import TYPE_CHECKING
from decimal import Decimal
from uuid import UUID

from sqlalchemy import ForeignKey, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base
from .mixins import CreatedAtMixin, UUIDPKMixin

if TYPE_CHECKING:
    from .users import User


class UserBalance(Base, UUIDPKMixin, CreatedAtMixin):
    """Баланс пользователя: доступные и удержанные токены."""

    __tablename__ = "user_balances"

    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id"), nullable=False, unique=True, index=True
    )
    available_tokens: Mapped[Decimal] = mapped_column(
        Numeric(18, 6), default=Decimal("0"), nullable=False
    )
    hold_tokens: Mapped[Decimal] = mapped_column(
        Numeric(18, 6), default=Decimal("0"), nullable=False
    )

    user: Mapped["User"] = relationship("User", back_populates="balance")
