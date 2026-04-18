from decimal import Decimal
from typing import TYPE_CHECKING, Any
from uuid import UUID

from sqlalchemy import Enum, ForeignKey, Numeric, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base
from .enums import BalanceTransactionType
from .mixins import CreatedAtMixin, UUIDPKMixin

if TYPE_CHECKING:
    from .users import User
    from .payment_transactions import PaymentTransaction
    from .plans import Plan


class BalanceTransaction(Base, UUIDPKMixin, CreatedAtMixin):
    __tablename__ = "balance_transactions"

    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    payment_transaction_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("payment_transactions.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    plan_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("plans.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    type: Mapped[BalanceTransactionType] = mapped_column(
        Enum(BalanceTransactionType, name="balance_transaction_type_enum"),
        nullable=False,
        index=True,
    )
    amount_tokens: Mapped[Decimal] = mapped_column(Numeric(18, 6), nullable=False)
    reason: Mapped[str | None] = mapped_column(String(255), nullable=True)
    meta_data: Mapped[dict[str, Any]] = mapped_column(
        JSONB, nullable=False, default=dict
    )

    user: Mapped["User"] = relationship("User", back_populates="balance_transactions")
    payment_transaction: Mapped["PaymentTransaction | None"] = relationship(
        "PaymentTransaction",
        back_populates="balance_transactions",
    )
    plan: Mapped["Plan | None"] = relationship(
        "Plan", back_populates="balance_transactions"
    )
