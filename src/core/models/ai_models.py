from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .mixins import UUIDPKMixin, CreatedAtMixin, ModelPricingMixin
from .base import Base

if TYPE_CHECKING:
    from .ai_generations import AIGeneration
    from .llm_configurations import LLMConfiguration


class AIModel(Base, UUIDPKMixin, CreatedAtMixin):
    __tablename__ = "ai_models"

    name: Mapped[str] = mapped_column(nullable=False)
    provider_key: Mapped[str] = mapped_column(nullable=False, unique=True)
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)
    description: Mapped[str | None] = mapped_column(nullable=True, default=None)

    llm_model: Mapped["LLMModel | None"] = relationship(
        back_populates="ai_model", cascade="all, delete-orphan", uselist=False
    )
    image_model: Mapped["ImageModel | None"] = relationship(
        back_populates="ai_model", cascade="all, delete-orphan", uselist=False
    )
    video_model: Mapped["VideoModel | None"] = relationship(
        back_populates="ai_model", cascade="all, delete-orphan", uselist=False
    )
    generations: Mapped[list["AIGeneration"]] = relationship(back_populates="ai_model")


class LLMModel(Base, UUIDPKMixin, CreatedAtMixin, ModelPricingMixin):
    __tablename__ = "llm_models"

    ai_model_id: Mapped[UUID] = mapped_column(
        ForeignKey("ai_models.id"), nullable=False, unique=True, index=True
    )
    input_price_per_million_usd: Mapped[float] = mapped_column(nullable=False)
    output_price_per_million_usd: Mapped[float] = mapped_column(nullable=False)
    min_charge_tokens: Mapped[int] = mapped_column(default=0, nullable=False)

    ai_model: Mapped["AIModel"] = relationship("AIModel", back_populates="llm_model")
    llm_configurations: Mapped[list["LLMConfiguration"]] = relationship(
        "LLMConfiguration",
        back_populates="llm_model",
        cascade="all, delete-orphan",
    )


class ImageModel(Base, UUIDPKMixin, CreatedAtMixin, ModelPricingMixin):
    __tablename__ = "image_models"

    ai_model_id: Mapped[UUID] = mapped_column(
        ForeignKey("ai_models.id"), nullable=False, unique=True, index=True
    )
    size: Mapped[str] = mapped_column(nullable=False)
    quality: Mapped[str] = mapped_column(nullable=False)
    style: Mapped[str | None] = mapped_column(nullable=True, default=None)
    images_count: Mapped[int] = mapped_column(default=1, nullable=False)

    ai_model: Mapped["AIModel"] = relationship("AIModel", back_populates="image_model")


class VideoModel(Base, UUIDPKMixin, CreatedAtMixin, ModelPricingMixin):
    __tablename__ = "video_models"

    ai_model_id: Mapped[UUID] = mapped_column(
        ForeignKey("ai_models.id"), nullable=False, unique=True, index=True
    )
    resolution: Mapped[str] = mapped_column(nullable=False)
    fps: Mapped[int | None] = mapped_column(nullable=True, default=None)
    price_per_second_usd: Mapped[float] = mapped_column(nullable=False)
    max_duration_seconds: Mapped[int | None] = mapped_column(nullable=True, default=None)

    ai_model: Mapped["AIModel"] = relationship("AIModel", back_populates="video_model")
