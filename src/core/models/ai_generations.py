from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import Enum, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base
from .enums import GenerationStatus
from .mixins import CreatedAtMixin, UUIDPKMixin

if TYPE_CHECKING:
    from .ai_models import AIModel
    from .users import User


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
    charged_tokens: Mapped[float] = mapped_column(nullable=False, default=0.0)

    user: Mapped["User"] = relationship("User", back_populates="generations")
    ai_model: Mapped["AIModel"] = relationship("AIModel", back_populates="generations")
