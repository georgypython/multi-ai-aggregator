from typing import TYPE_CHECKING
from decimal import Decimal
from uuid import UUID
from datetime import datetime

from sqlalchemy import Enum, ForeignKey, DateTime, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base
from .enums import GenerationStatus, GenerationType
from .mixins import CreatedAtMixin, UUIDPKMixin

if TYPE_CHECKING:
    from .ai_models import AIModel
    from .users import User
    from .media_files import MediaFile


class AIGeneration(Base, UUIDPKMixin, CreatedAtMixin):
    __tablename__ = "ai_generations"

    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id"), nullable=False, index=True
    )
    ai_model_id: Mapped[UUID] = mapped_column(
        ForeignKey("ai_models.id"), nullable=False, index=True
    )
    status: Mapped[GenerationStatus] = mapped_column(
        Enum(GenerationStatus, name="generation_status_enum"), nullable=False
    )
    generation_type: Mapped[GenerationType] = mapped_column(
        Enum(GenerationType, name="generation_type_enum"), nullable=False
    )
    task_id: Mapped[str | None] = mapped_column(nullable=True)
    result_url: Mapped[str | None] = mapped_column(nullable=True)
    hold_tokens_amount: Mapped[Decimal] = mapped_column(
        Numeric(18, 6), nullable=False, default=Decimal("0")
    )
    charged_tokens: Mapped[Decimal] = mapped_column(
        Numeric(18, 6), nullable=False, default=Decimal("0")
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    user: Mapped["User"] = relationship("User", back_populates="generations")
    ai_model: Mapped["AIModel"] = relationship("AIModel", back_populates="generations")
    media_files: Mapped[list["MediaFile"]] = relationship(back_populates="generation")
