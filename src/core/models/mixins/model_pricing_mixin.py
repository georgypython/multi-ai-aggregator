from sqlalchemy.orm import Mapped, mapped_column


class ModelPricingMixin:
    min_charge_tokens: Mapped[int] = mapped_column(default=0, nullable=False)
    free_requests_limit: Mapped[int] = mapped_column(default=0, nullable=False)