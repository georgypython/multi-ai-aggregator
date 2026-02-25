from typing import TYPE_CHECKING

from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base
from .mixins import CreatedAtMixin, UUIDPKMixin

if TYPE_CHECKING:
    from .ai_generations import AIGeneration


class User(Base, UUIDPKMixin, CreatedAtMixin):
    __tablename__ = "users"

    token_balances: Mapped[float] = mapped_column(default=0.0, nullable=False)
    generations: Mapped[list["AIGeneration"]] = relationship(back_populates="user")
