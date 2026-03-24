from typing import TYPE_CHECKING
from decimal import Decimal
from uuid import UUID

from sqlalchemy import ForeignKey, Enum, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .enums import ModelType
from .mixins import UUIDPKMixin, CreatedAtMixin
from .base import Base

if TYPE_CHECKING:
    from .ai_generations import AIGeneration
    from .model_profiles import ImageProfile, VideoProfile, LLMProfile
    from .token_prices import TokenPrice


class AIModel(Base, UUIDPKMixin, CreatedAtMixin):
    """Справочник AI-моделей и базовых лимитов/тарифов."""

    __tablename__ = "ai_models"

    name: Mapped[str] = mapped_column(nullable=False)
    provider_key: Mapped[str] = mapped_column(nullable=False, unique=True)
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)
    description: Mapped[str | None] = mapped_column(nullable=True, default=None)
    model_type: Mapped[ModelType] = mapped_column(
        Enum(ModelType, name="model_type_enum"), nullable=False
    )
    token_price_id: Mapped[UUID] = mapped_column(
        ForeignKey("token_prices.id"), nullable=False
    )
    min_charge_tokens: Mapped[Decimal] = mapped_column(
        Numeric(18, 6), default=Decimal("0"), nullable=False
    )
    free_requests_limit: Mapped[int] = mapped_column(default=0, nullable=False)

    llm_profile: Mapped["LLMProfile | None"] = relationship(
        back_populates="ai_model", cascade="all, delete-orphan", uselist=False
    )
    image_profile: Mapped["ImageProfile | None"] = relationship(
        back_populates="ai_model", cascade="all, delete-orphan", uselist=False
    )
    video_profile: Mapped["VideoProfile | None"] = relationship(
        back_populates="ai_model", cascade="all, delete-orphan", uselist=False
    )
    generations: Mapped[list["AIGeneration"]] = relationship(back_populates="ai_model")
    token_price: Mapped["TokenPrice"] = relationship(back_populates="ai_models")
