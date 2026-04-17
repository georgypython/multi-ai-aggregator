from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import Boolean, Enum, ForeignKey, Integer, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base
from .enums import PaymentMethod
from .mixins import CreatedAtMixin, UUIDPKMixin

if TYPE_CHECKING:
    from .payment_provider_configs import PaymentProviderConfig


class PaymentProviderMethod(Base, UUIDPKMixin, CreatedAtMixin):
    __tablename__ = "payment_provider_methods"
    __table_args__ = (
        UniqueConstraint("provider_id", "method_code", name="uq_provider_method"),
    )

    provider_id: Mapped[UUID] = mapped_column(
        ForeignKey("payment_provider_configs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    method_code: Mapped[PaymentMethod] = mapped_column(
        Enum(PaymentMethod, name="payment_method_enum"),
        nullable=False,
        index=True,
    )
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    is_soon: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    provider: Mapped["PaymentProviderConfig"] = relationship(
        "PaymentProviderConfig",
        back_populates="methods",
    )
