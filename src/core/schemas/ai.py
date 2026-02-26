from pydantic import BaseModel
from uuid import UUID

from src.core.models.enums import ProviderType


class LLMRequestDataSchema(BaseModel):
    user_id: UUID
    ai_model_id: UUID
    provider_model_key: str
    prompt: str
