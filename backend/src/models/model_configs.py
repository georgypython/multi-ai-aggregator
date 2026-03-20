from typing import TYPE_CHECKING
from decimal import Decimal
from uuid import UUID

from sqlalchemy import Enum, ForeignKey, Numeric, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base
from .enums import ModelProvider
from .mixins import CreatedAtMixin, UUIDPKMixin

if TYPE_CHECKING:
    from .ai_models import AIModel


class LLMProfile(Base, UUIDPKMixin, CreatedAtMixin):
    __tablename__ = "llm_profiles"

    ai_model_id: Mapped[UUID] = mapped_column(
        ForeignKey("ai_models.id"), nullable=False, unique=True, index=True
    )
    input_price_per_million_usd: Mapped[Decimal] = mapped_column(
        Numeric(18, 10), nullable=False
    )
    output_price_per_million_usd: Mapped[Decimal] = mapped_column(
        Numeric(18, 10), nullable=False
    )
    is_temperature_support: Mapped[bool | None] = mapped_column(
        nullable=True, default=False
    )

    ai_model: Mapped["AIModel"] = relationship("AIModel", back_populates="llm_profile")


class ImageProfile(Base, UUIDPKMixin, CreatedAtMixin):
    __tablename__ = "image_profiles"

    ai_model_id: Mapped[UUID] = mapped_column(
        ForeignKey("ai_models.id"), nullable=False, unique=True, index=True
    )
    provider: Mapped[ModelProvider] = mapped_column(
        Enum(ModelProvider, name="model_provider_enum"), nullable=False
    )
    image_edit_model_name: Mapped[str | None] = mapped_column(
        nullable=True, default=None
    )
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)

    ai_model: Mapped["AIModel"] = relationship(back_populates="image_profile")
    prices: Mapped[list["ImagePrice"]] = relationship(
        back_populates="image_profile", cascade="all, delete-orphan"
    )


class VideoProfile(Base, UUIDPKMixin, CreatedAtMixin):
    __tablename__ = "video_profiles"

    ai_model_id: Mapped[UUID] = mapped_column(
        ForeignKey("ai_models.id"), nullable=False, unique=True, index=True
    )
    provider: Mapped[ModelProvider] = mapped_column(
        Enum(ModelProvider, name="model_provider_enum"), nullable=False
    )
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)

    ai_model: Mapped["AIModel"] = relationship(back_populates="video_profile")
    prices: Mapped[list["VideoPrice"]] = relationship(
        back_populates="video_profile", cascade="all, delete-orphan"
    )


class ImagePrice(Base, UUIDPKMixin, CreatedAtMixin):
    __tablename__ = "image_prices"
    __table_args__ = (
        UniqueConstraint(
            "image_profile_id", "quality", "size", name="uq_image_price_combo"
        ),
    )

    image_profile_id: Mapped[UUID] = mapped_column(
        ForeignKey("image_profiles.id"), nullable=False, index=True
    )
    quality: Mapped[str] = mapped_column(nullable=False)
    size: Mapped[str] = mapped_column(nullable=False)
    provider_cost: Mapped[Decimal] = mapped_column(Numeric(18, 10), nullable=False)

    image_profile: Mapped["ImageProfile"] = relationship(back_populates="prices")


class VideoPrice(Base, UUIDPKMixin, CreatedAtMixin):
    __tablename__ = "video_prices"
    __table_args__ = (
        UniqueConstraint(
            "video_profile_id", "duration_seconds", "size", name="uq_video_price_combo"
        ),
    )

    video_profile_id: Mapped[UUID] = mapped_column(
        ForeignKey("video_profiles.id"), nullable=False, index=True
    )
    duration_seconds: Mapped[int] = mapped_column(nullable=False)
    size: Mapped[str] = mapped_column(nullable=False)
    provider_cost: Mapped[Decimal] = mapped_column(Numeric(18, 10), nullable=False)

    video_profile: Mapped["VideoProfile"] = relationship(back_populates="prices")
