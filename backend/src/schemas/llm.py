from decimal import Decimal
from typing import Any

from pydantic import BaseModel

from .generations import GenerationRequestSchema


class LLMRequestDataSchema(GenerationRequestSchema):
    input_price_per_million_usd: Decimal | None = None
    output_price_per_million_usd: Decimal | None = None
    temperature: float | None = None
    instructions: str | None = None


class LLMGenerationCreateRequestSchema(BaseModel):
    prompt: str


class LLMProviderResponseSchema(BaseModel):
    text: str
    model: str
    input_tokens: int
    output_tokens: int
    total_tokens: int
    raw: dict[str, Any]
