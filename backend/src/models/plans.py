from decimal import Decimal
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import Boolean, Enum, ForeignKey, Numeric, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base
from .enums import BillingInterval
from .mixins import CreatedAtMixin, UUIDPKMixin

if TYPE_CHECKING:
    from .products import Product
    from .orders import Order
    from .subscriptions import Subscription
    from .balance_transactions import BalanceTransaction


class Plan(Base, UUIDPKMixin, CreatedAtMixin):
    __tablename__ = "plans"

    product_id: Mapped[UUID] = mapped_column(
        ForeignKey("products.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    billing_interval: Mapped[BillingInterval] = mapped_column(
        Enum(BillingInterval, name="billing_interval_enum"),
        nullable=False,
        default=BillingInterval.MONTHLY,
    )
    duration_days: Mapped[int] = mapped_column(nullable=False, default=30)

    price_rub: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    tokens_amount: Mapped[Decimal] = mapped_column(Numeric(18, 6), nullable=False)

    lavatop_recurring_offer_id: Mapped[UUID | None] = mapped_column(nullable=True)
    lavatop_recurring_product_id: Mapped[UUID | None] = mapped_column(nullable=True)
    lavatop_one_time_offer_id: Mapped[UUID | None] = mapped_column(nullable=True)
    lavatop_one_time_product_id: Mapped[UUID | None] = mapped_column(nullable=True)

    available_payment_methods: Mapped[list[str]] = mapped_column(
        JSONB,
        nullable=False,
        default=list,
    )
    is_vpn_bonus_enabled: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )
    display_name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    llm_max_limit: Mapped[int] = mapped_column(nullable=False, default=0)
    image_max_limit: Mapped[int] = mapped_column(nullable=False, default=0)
    video_max_limit: Mapped[int] = mapped_column(nullable=False, default=0)

    product: Mapped["Product"] = relationship("Product", back_populates="plans")
    orders: Mapped[list["Order"]] = relationship("Order", back_populates="plan")
    subscriptions: Mapped[list["Subscription"]] = relationship(
        "Subscription",
        back_populates="plan",
    )
    balance_transactions: Mapped[list["BalanceTransaction"]] = relationship(
        "BalanceTransaction",
        back_populates="plan",
    )
