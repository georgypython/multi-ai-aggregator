from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import BigInteger

from .base import Base
from .mixins import CreatedAtMixin, UUIDPKMixin

if TYPE_CHECKING:
    from .ai_generations import AIGeneration
    from .llm_configurations import LLMConfiguration
    from .user_balances import UserBalance
    from .media_files import MediaFile


class User(Base, UUIDPKMixin, CreatedAtMixin):
    __tablename__ = "users"

    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, nullable=False)
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)

    balance: Mapped["UserBalance | None"] = relationship(
        back_populates="user", cascade="all, delete-orphan", uselist=False
    )
    llm_configuration: Mapped["LLMConfiguration"] = relationship(back_populates="user")
    generations: Mapped[list["AIGeneration"]] = relationship(back_populates="user")
    media_files: Mapped[list["MediaFile"]] = relationship(back_populates="user")