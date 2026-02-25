from typing import TYPE_CHECKING

from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Enum

from .mixins import UUIDPKMixin, CreatedAtMixin
from .base import Base
from .enums import ProviderType, AIModelType

if TYPE_CHECKING:
    from .ai_generations import AIGeneration
    from .ai_prices import ImagePrice, LLMPrice, VideoPrice


class AIModel(Base, UUIDPKMixin, CreatedAtMixin):
    __tablename__ = "ai_models"

    name: Mapped[str] = mapped_column(nullable=False)
    model_type: Mapped[AIModelType] = mapped_column(
        Enum(AIModelType, name="model_type_enum"), nullable=False,
    )
    provider: Mapped[ProviderType] = mapped_column(
        Enum(ProviderType, name="provider_type_enum"), nullable=False,
    )
    provider_key: Mapped[str] = mapped_column(nullable=False, unique=True)
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)
    description: Mapped[str | None] = mapped_column(nullable=True, default=None)
    
    llm_prices: Mapped[list["LLMPrice"]] = relationship(
        back_populates="ai_model", cascade="all, delete-orphan"
    )
    image_prices: Mapped[list["ImagePrice"]] = relationship(
        back_populates="ai_model", cascade="all, delete-orphan"
    )
    video_prices: Mapped[list["VideoPrice"]] = relationship(
        back_populates="ai_model", cascade="all, delete-orphan"
    )
    generations: Mapped[list["AIGeneration"]] = relationship(back_populates="ai_model")