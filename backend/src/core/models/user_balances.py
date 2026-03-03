from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base
from .mixins import CreatedAtMixin, UUIDPKMixin

if TYPE_CHECKING:
    from .users import User


class UserBalance(Base, UUIDPKMixin, CreatedAtMixin):
    __tablename__ = "user_balances"

    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id"), nullable=False, unique=True, index=True
    )
    available_tokens: Mapped[float] = mapped_column(default=0.0, nullable=False)
    hold_tokens: Mapped[float] = mapped_column(default=0.0, nullable=False)

    user: Mapped["User"] = relationship("User", back_populates="balance")
