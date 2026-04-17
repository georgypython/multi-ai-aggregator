from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Any
from uuid import UUID

from sqlalchemy import DateTime, Enum, ForeignKey, Numeric
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base
from .enums import OrderStatus, PaymentCurrency, ProductPaymentType
from .mixins import CreatedAtMixin, UUIDPKMixin

if TYPE_CHECKING:
    from .plans import Plan
    from .users import User
    from .payment_intents import PaymentIntent


class Order(Base, UUIDPKMixin, CreatedAtMixin):
    __tablename__ = "orders"

    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    plan_id: Mapped[UUID] = mapped_column(
        ForeignKey("plans.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    payment_type: Mapped[ProductPaymentType] = mapped_column(
        Enum(ProductPaymentType, name="product_payment_type_enum"),
        nullable=False,
    )
    amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    currency: Mapped[PaymentCurrency] = mapped_column(
        Enum(PaymentCurrency, name="payment_currency_enum"),
        nullable=False,
        default=PaymentCurrency.RUB,
    )
    discount_amount: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        nullable=False,
        default=Decimal("0"),
    )

    status: Mapped[OrderStatus] = mapped_column(
        Enum(OrderStatus, name="order_status_enum"),
        nullable=False,
        default=OrderStatus.PENDING,
        index=True,
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    paid_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    meta_data: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)

    user: Mapped["User"] = relationship("User", back_populates="orders")
    plan: Mapped["Plan"] = relationship("Plan", back_populates="orders")
    payment_intents: Mapped[list["PaymentIntent"]] = relationship(
        "PaymentIntent",
        back_populates="order",
        cascade="all, delete-orphan",
    )
