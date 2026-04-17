from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Enum, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base
from .enums import TariffCode
from .mixins import CreatedAtMixin, UUIDPKMixin

if TYPE_CHECKING:
    from .plans import Plan


class Product(Base, UUIDPKMixin, CreatedAtMixin):
    __tablename__ = "products"

    code: Mapped[TariffCode] = mapped_column(
        Enum(TariffCode, name="tariff_code_enum"),
        nullable=False,
        unique=True,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    plans: Mapped[list["Plan"]] = relationship(
        "Plan",
        back_populates="product",
        cascade="all, delete-orphan",
    )
