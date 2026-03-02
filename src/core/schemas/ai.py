from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field
from uuid import UUID

from src.core.models.enums import LLMConfigurationType, ModelType


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


class GenerationRequestSchema(BaseModel):
    user_id: UUID
    ai_model_id: UUID
    min_charge_tokens: float
    free_requests_limit: int = 0


class GenerationResultSchema(BaseModel):
    user_id: UUID
    generation_id: UUID
    hold_amount: float
    provider_cost: float


class GenerationRequestSchema(BaseModel):
    user_id: UUID
    ai_model_id: UUID
    min_charge_tokens: float
    free_requests_limit: int = 0


class GenerationResultSchema(BaseModel):
    user_id: UUID
    generation_id: UUID
    hold_amount: float
    provider_cost: float


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


class AIModelListItemResponseSchema(BaseModel):
    id: UUID
    name: str
    provider_key: str
    is_active: bool
    description: str | None
    model_type: ModelType
    created_at: datetime


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
