from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import BaseModel


class LLMRequestDataSchema(BaseModel):
    user_id: UUID
    ai_model_id: UUID
    provider_model_key: str
    prompt: str
    model_token_price_id: UUID
    min_charge_tokens: Decimal
    free_requests_limit: int = 0
    input_price_per_million_usd: Decimal | None = None
    output_price_per_million_usd: Decimal | None = None
    temperature: float | None
    instructions: str | None


class LLMGenerationCreateRequestSchema(BaseModel):
    prompt: str


class LLMProviderResponseSchema(BaseModel):
    text: str
    model: str
    input_tokens: int
    output_tokens: int
    total_tokens: int
    raw: dict[str, Any]
