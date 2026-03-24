from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from src.models.enums import LLMConfigurationType


class LLMConfigCreateRequestSchema(BaseModel):
    name: str | None = None
    temperature: float | None = Field(default=None, ge=0.0, le=2.0)
    instructions: str | None = None


class LLMConfigResponseSchema(BaseModel):
    id: UUID
    user_id: UUID | None
    name: str | None
    configuration_type: LLMConfigurationType
    temperature: float | None
    instructions: str | None
    created_at: datetime
