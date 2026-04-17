from typing import TYPE_CHECKING, Any
from uuid import UUID

from sqlalchemy import Enum, ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base
from .enums import PaymentIntentStatus, PaymentProvider
from .mixins import CreatedAtMixin, UUIDPKMixin

if TYPE_CHECKING:
    from .orders import Order
    from .payment_transactions import PaymentTransaction


class PaymentIntent(Base, UUIDPKMixin, CreatedAtMixin):
    __tablename__ = "payment_intents"

    order_id: Mapped[UUID] = mapped_column(
        ForeignKey("orders.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    provider: Mapped[PaymentProvider] = mapped_column(
        Enum(PaymentProvider, name="payment_provider_enum"),
        nullable=False,
        index=True,
    )

    provider_invoice_id: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    provider_contract_id: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        index=True,
    )
    provider_offer_id: Mapped[str | None] = mapped_column(String(255), nullable=True)

    status: Mapped[PaymentIntentStatus] = mapped_column(
        Enum(PaymentIntentStatus, name="payment_intent_status_enum"),
        nullable=False,
        default=PaymentIntentStatus.CREATED,
        index=True,
    )

    invoice_url: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    provider_data: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)

    order: Mapped["Order"] = relationship("Order", back_populates="payment_intents")
    transactions: Mapped[list["PaymentTransaction"]] = relationship(
        "PaymentTransaction",
        back_populates="payment_intent",
        cascade="all, delete-orphan",
    )
