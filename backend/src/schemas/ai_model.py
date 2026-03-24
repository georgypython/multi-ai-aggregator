from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from src.models.enums import ModelType


class AIModelListItemResponseSchema(BaseModel):
    id: UUID
    name: str
    provider_key: str
    is_active: bool
    description: str | None
    model_type: ModelType
    created_at: datetime
