from decimal import Decimal
from typing import TYPE_CHECKING, Any
from uuid import UUID

from sqlalchemy import Enum, ForeignKey, Numeric, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base
from .enums import PaymentCurrency, TransactionStatus, TransactionType
from .mixins import CreatedAtMixin, UUIDPKMixin

if TYPE_CHECKING:
    from .users import User
    from .subscriptions import Subscription
    from .payment_intents import PaymentIntent
    from .balance_transactions import BalanceTransaction


class PaymentTransaction(Base, UUIDPKMixin, CreatedAtMixin):
    __tablename__ = "payment_transactions"

    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    payment_intent_id: Mapped[UUID] = mapped_column(
        ForeignKey("payment_intents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    subscription_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("subscriptions.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    type: Mapped[TransactionType] = mapped_column(
        Enum(TransactionType, name="transaction_type_enum"),
        nullable=False,
        index=True,
    )
    amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    currency: Mapped[PaymentCurrency] = mapped_column(
        Enum(PaymentCurrency, name="payment_currency_enum"),
        nullable=False,
        default=PaymentCurrency.RUB,
    )
    status: Mapped[TransactionStatus] = mapped_column(
        Enum(TransactionStatus, name="transaction_status_enum"),
        nullable=False,
        index=True,
    )

    provider_transaction_id: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        unique=True,
        index=True,
    )
    provider_data: Mapped[dict[str, Any]] = mapped_column(
        JSONB, nullable=False, default=dict
    )

    parent_transaction_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("payment_transactions.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    description: Mapped[str | None] = mapped_column(String(500), nullable=True)
    error_message: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    meta_data: Mapped[dict[str, Any]] = mapped_column(
        JSONB, nullable=False, default=dict
    )

    user: Mapped["User"] = relationship("User", back_populates="payment_transactions")
    payment_intent: Mapped["PaymentIntent"] = relationship(
        "PaymentIntent",
        back_populates="transactions",
    )
    subscription: Mapped["Subscription | None"] = relationship(
        "Subscription",
        back_populates="transactions",
    )
    parent_transaction: Mapped["PaymentTransaction | None"] = relationship(
        "PaymentTransaction",
        remote_side="PaymentTransaction.id",
        back_populates="refunds",
    )
    refunds: Mapped[list["PaymentTransaction"]] = relationship(
        "PaymentTransaction",
        back_populates="parent_transaction",
    )
    balance_transactions: Mapped[list["BalanceTransaction"]] = relationship(
        "BalanceTransaction",
        back_populates="payment_transaction",
    )
