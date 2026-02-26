from typing import TYPE_CHECKING

from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base
from .mixins import CreatedAtMixin, UUIDPKMixin

if TYPE_CHECKING:
    from .ai_generations import AIGeneration
    from .user_balances import UserBalance


class User(Base, UUIDPKMixin, CreatedAtMixin):
    __tablename__ = "users"

    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)

    balance: Mapped["UserBalance | None"] = relationship(
        back_populates="user", cascade="all, delete-orphan", uselist=False
    )
    generations: Mapped[list["AIGeneration"]] = relationship(back_populates="user")
