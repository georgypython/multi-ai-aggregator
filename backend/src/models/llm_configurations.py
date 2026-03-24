from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import Enum, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base
from .enums import LLMConfigurationType
from .mixins import CreatedAtMixin, UUIDPKMixin

if TYPE_CHECKING:
    from .users import User


class LLMConfiguration(Base, UUIDPKMixin, CreatedAtMixin):
    """Пользовательские настройки поведения LLM."""

    __tablename__ = "llm_configurations"

    name: Mapped[str | None] = mapped_column(nullable=True, default=None)
    user_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("users.id"), nullable=True, index=True
    )
    configuration_type: Mapped[LLMConfigurationType] = mapped_column(
        Enum(LLMConfigurationType, name="llm_configuration_type_enum"), nullable=False
    )
    temperature: Mapped[float | None] = mapped_column(nullable=True, default=None)
    instructions: Mapped[str | None] = mapped_column(nullable=True, default=None)

    user: Mapped["User | None"] = relationship(
        "User", back_populates="llm_configuration"
    )
