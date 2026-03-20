from typing import TYPE_CHECKING
from uuid import UUID
from datetime import datetime

from sqlalchemy import ForeignKey, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base
from .mixins import CreatedAtMixin, UUIDPKMixin

if TYPE_CHECKING:
    from .users import User
    from .ai_generations import AIGeneration


class MediaFile(Base, UUIDPKMixin, CreatedAtMixin):
    """Метаданные загруженного пользователем медиафайла."""

    __tablename__ = "media_files"

    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    generation_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("ai_generations.id"),
        nullable=True,
    )
    object_key: Mapped[str] = mapped_column(nullable=False)
    content_type: Mapped[str] = mapped_column(nullable=False)
    size_bytes: Mapped[int] = mapped_column(nullable=False)
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )

    user: Mapped["User"] = relationship("User", back_populates="media_files")
    generation: Mapped["AIGeneration | None"] = relationship(
        back_populates="media_files",
    )
