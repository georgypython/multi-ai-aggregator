from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import ForeignKey, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .enums import ModelType
from .mixins import UUIDPKMixin, CreatedAtMixin
from .base import Base

if TYPE_CHECKING:
    from .ai_generations import AIGeneration


class AIModel(Base, UUIDPKMixin, CreatedAtMixin):
    __tablename__ = "ai_models"

    name: Mapped[str] = mapped_column(nullable=False)
    provider_key: Mapped[str] = mapped_column(nullable=False, unique=True)
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)
    description: Mapped[str | None] = mapped_column(nullable=True, default=None)
    model_type: Mapped[ModelType] = mapped_column(
        Enum(ModelType, name="model_type_enum"), nullable=False
    )
    min_charge_tokens: Mapped[int] = mapped_column(default=0, nullable=False)
    free_requests_limit: Mapped[int] = mapped_column(default=0, nullable=False)
    images_edit_support: Mapped[bool] = mapped_column(default=False, nullable=False)

    llm_model: Mapped["LLMModel | None"] = relationship(
        back_populates="ai_model", cascade="all, delete-orphan", uselist=False
    )
    generations: Mapped[list["AIGeneration"]] = relationship(back_populates="ai_model")


class LLMModel(Base, UUIDPKMixin, CreatedAtMixin):
    __tablename__ = "llm_models"

    ai_model_id: Mapped[UUID] = mapped_column(
        ForeignKey("ai_models.id"), nullable=False, unique=True, index=True
    )
    input_price_per_million_usd: Mapped[float] = mapped_column(nullable=False)
    output_price_per_million_usd: Mapped[float] = mapped_column(nullable=False)
    is_temperature_support: Mapped[bool | None] = mapped_column(
        nullable=True, default=False
    )

    ai_model: Mapped["AIModel"] = relationship("AIModel", back_populates="llm_model")
