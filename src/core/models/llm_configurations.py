from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import Enum, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base
from .enums import LLMConfigurationType
from .mixins import CreatedAtMixin, UUIDPKMixin

if TYPE_CHECKING:
    from .ai_models import LLMModel
    from .users import User


class LLMConfiguration(Base, UUIDPKMixin, CreatedAtMixin):
    __tablename__ = "llm_configurations"

    name: Mapped[str | None] = mapped_column(nullable=True, default=None)
    llm_model_id: Mapped[UUID] = mapped_column(
        ForeignKey("llm_models.id"), nullable=False, index=True
    )
    user_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("users.id"), nullable=True, index=True
    )
    configuration_type: Mapped[LLMConfigurationType] = mapped_column(
        Enum(LLMConfigurationType, name="llm_configuration_type_enum"), nullable=False
    )
    temperature: Mapped[float | None] = mapped_column(nullable=True, default=None)
    instructions: Mapped[str | None] = mapped_column(nullable=True, default=None)

    llm_model: Mapped["LLMModel"] = relationship("LLMModel", back_populates="llm_configurations")
    user: Mapped["User | None"] = relationship("User", back_populates="llm_configurations")
