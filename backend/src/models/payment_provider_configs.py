from typing import TYPE_CHECKING

from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base
from .mixins import CreatedAtMixin, UUIDPKMixin

if TYPE_CHECKING:
    from .payment_provider_methods import PaymentProviderMethod


class PaymentProviderConfig(Base, UUIDPKMixin, CreatedAtMixin):
    __tablename__ = "payment_provider_configs"

    code: Mapped[str] = mapped_column(
        String(50), nullable=False, unique=True, index=True
    )
    display_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    methods: Mapped[list["PaymentProviderMethod"]] = relationship(
        "PaymentProviderMethod",
        back_populates="provider",
        cascade="all, delete-orphan",
    )
