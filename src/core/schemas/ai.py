from typing import Any

from pydantic import BaseModel
from uuid import UUID


class LLMRequestDataSchema(BaseModel):
    user_id: UUID
    ai_model_id: UUID
    provider_model_key: str
    prompt: str
    min_charge_tokens: float
    free_requests_limit: int = 0
    input_price_per_million_usd: float | None = None
    output_price_per_million_usd: float | None = None
    temperature: float | None
    instructions: str | None


class LLMProviderResponseSchema(BaseModel):
    text: str
    model: str
    input_tokens: int
    output_tokens: int
    total_tokens: int
    provider_cost: float | None = None
    raw: dict[str, Any]


class LLMResultResponseSchema(BaseModel):
    text: str
    ai_model_id: UUID
    user_id: UUID
    generation_id: UUID
    tokens_cost: float
