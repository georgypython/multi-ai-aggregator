from sqlalchemy import Enum
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base
from .enums import PriceType
from .mixins import CreatedAtMixin, UUIDPKMixin


class TokenPrice(Base, UUIDPKMixin, CreatedAtMixin):
    __tablename__ = "token_prices"

    price_type: Mapped[PriceType] = mapped_column(
        Enum(PriceType, name="price_type_enum"), nullable=False, index=True
    )
    usd_per_token: Mapped[float] = mapped_column(nullable=False)
    rub_per_token: Mapped[float | None] = mapped_column(nullable=True, default=None)
    provider_cost_multiplier: Mapped[float | None] = mapped_column(
        nullable=True, default=None
    )
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)
