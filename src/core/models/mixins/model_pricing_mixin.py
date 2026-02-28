from sqlalchemy.orm import Mapped, mapped_column


class ModelPricingMixin:
    provider_price_usd: Mapped[float] = mapped_column(nullable=False)
    our_price_tokens: Mapped[int] = mapped_column(nullable=False)
    min_req_tokens: Mapped[int] = mapped_column(default=0, nullable=False)
