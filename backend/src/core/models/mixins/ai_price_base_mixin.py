from decimal import Decimal
from uuid import UUID

from sqlalchemy import ForeignKey, Numeric
from sqlalchemy.orm import Mapped, mapped_column


class AIPriceBaseMixin:
    ai_model_id: Mapped[UUID] = mapped_column(
        ForeignKey("ai_models.id"), nullable=False, unique=True
    )
    provider_price_usd: Mapped[Decimal] = mapped_column(Numeric(12, 6), nullable=False)
    our_price_tokens: Mapped[int] = mapped_column(nullable=False)
    min_req_tokens: Mapped[int] = mapped_column(default=0, nullable=False)
    approximate_const: Mapped[int | None] = mapped_column(default=None, nullable=True)
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)
