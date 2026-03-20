from typing import TYPE_CHECKING
from decimal import Decimal

from sqlalchemy import Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base
from .mixins import CreatedAtMixin, UUIDPKMixin

if TYPE_CHECKING:
    from .ai_models import AIModel


class TokenPrice(Base, UUIDPKMixin, CreatedAtMixin):
    """Курс токена и коэффициенты пересчета стоимости провайдера."""

    __tablename__ = "token_prices"

    usd_per_token: Mapped[Decimal] = mapped_column(Numeric(18, 10), nullable=False)
    rub_per_token: Mapped[Decimal | None] = mapped_column(
        Numeric(18, 10), nullable=True, default=None
    )
    provider_cost_multiplier: Mapped[Decimal | None] = mapped_column(
        Numeric(18, 10), nullable=True, default=None
    )
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)

    ai_models: Mapped[list["AIModel | None"]] = relationship(
        back_populates="token_price"
    )
