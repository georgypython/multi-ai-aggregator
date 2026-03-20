from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel

from src.models.enums import GenerationStatus, GenerationType


class GenerationRequestSchema(BaseModel):
    user_id: UUID
    ai_model_id: UUID
    generation_type: GenerationType
    hold_amount: Decimal
    free_requests_limit: int = 0


class GenerationResultSchema(BaseModel):
    user_id: UUID
    generation_id: UUID
    hold_amount: Decimal
    provider_cost: Decimal
    result_url: str | None = None


class GenerationFinishData(BaseModel):
    ai_model_id: UUID
    generation_id: UUID
    user_id: UUID
    generation_type: GenerationType
    model_token_price_id: UUID
    hold_amount: Decimal
    provider_cost: Decimal
    provider_status: GenerationStatus
    result_url: str | None = None
    text: str | None = None


class GenerationResultResponseDataSchema(BaseModel):
    ai_model_id: UUID
    user_id: UUID
    generation_id: UUID
    tokens_cost: Decimal
    status: GenerationStatus
    text: str | None = None


class PollWaveSpeedGenerationTaskSchema(BaseModel):
    ai_model_id: UUID
    user_id: UUID
    generation_id: UUID
    generation_type: GenerationType
    model_token_price_id: UUID
    hold_amount: Decimal
    provider_cost: Decimal
    wavespeed_task_id: str
    poll_interval_seconds: int = 5
    max_attempts: int = 120
    current_attempt: int = 1
    timeout: int = 30
    final_tokens_cost: Decimal
    result_url: str | None
