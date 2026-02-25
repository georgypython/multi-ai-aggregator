from typing import TYPE_CHECKING

from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base
from .mixins import AIPriceBaseMixin, CreatedAtMixin, UUIDPKMixin

if TYPE_CHECKING:
	from .ai_models import AIModel


class LLMPrice(Base, UUIDPKMixin, CreatedAtMixin, AIPriceBaseMixin):
	__tablename__ = "llm_prices"

	input_price_per_million_usd: Mapped[float] = mapped_column(nullable=False)
	output_price_per_million_usd: Mapped[float] = mapped_column(nullable=False)
	min_charge_tokens: Mapped[int] = mapped_column(default=0, nullable=False)

	ai_model: Mapped["AIModel"] = relationship("AIModel", back_populates="llm_prices")


class ImagePrice(Base, UUIDPKMixin, CreatedAtMixin, AIPriceBaseMixin):
	__tablename__ = "image_prices"

	size: Mapped[str] = mapped_column(String(32), nullable=False)
	quality: Mapped[str] = mapped_column(String(32), nullable=False)
	style: Mapped[str | None] = mapped_column(String(32), nullable=True, default=None)
	images_count: Mapped[int] = mapped_column(Integer, default=1, nullable=False)

	ai_model: Mapped["AIModel"] = relationship("AIModel", back_populates="image_prices")


class VideoPrice(Base, UUIDPKMixin, CreatedAtMixin, AIPriceBaseMixin):
	__tablename__ = "video_prices"

	resolution: Mapped[str] = mapped_column(String(32), nullable=False)
	fps: Mapped[int | None] = mapped_column(Integer, nullable=True, default=None)
	price_per_second_usd: Mapped[float] = mapped_column(nullable=False)
	max_duration_seconds: Mapped[int | None] = mapped_column(
		Integer, nullable=True, default=None
	)

	ai_model: Mapped["AIModel"] = relationship("AIModel", back_populates="video_prices")

