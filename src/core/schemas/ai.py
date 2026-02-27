from typing import Any

from pydantic import BaseModel
from uuid import UUID


class LLMRequestDataSchema(BaseModel):
    user_id: UUID
    ai_model_id: UUID
    provider_model_key: str
    prompt: str
    min_charge_tokens: float


class LLMProviderResponseSchema(BaseModel):
    text: str
    model: str
    input_tokens: int
    output_tokens: int
    total_tokens: int
    raw: dict[str, Any]
