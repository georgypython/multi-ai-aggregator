from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel

from src.models.enums import GenerationStatus, GenerationType, ModelType


class GenerationCreateRequestSchema(BaseModel):
    prompt: str
    model_type: ModelType
    size: str | None
    quality: str | None
    duration_seconds: int | None
    media_file_ids: list[UUID] | None = None


class GenerationRequestSchema(BaseModel):
    user_id: UUID
    ai_model_id: UUID
    generation_type: GenerationType
    hold_amount: Decimal
    prompt: str
    provider_model_key: str
    model_token_price_id: UUID
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
    hold_amount: Decimal
    final_tokens_cost: Decimal
    provider_status: GenerationStatus
    result_url: str | None = None
    text: str | None = None


class GenerationResultResponseDataSchema(BaseModel):
    ai_model_id: UUID
    user_id: UUID
    generation_id: UUID
    tokens_cost: Decimal
    status: GenerationStatus
    is_free_request: bool
    text: str | None = None


class PollDbGenerationTaskSchema(BaseModel):
    poll_interval_seconds: int = 3
    max_attempts: int = 30
    current_attempt: int = 1
    user_tg_id: int
    ai_model_id: UUID
    user_id: UUID
    generation_id: UUID
    generation_type: GenerationType
    model_token_price_id: UUID
    hold_amount: Decimal
    provider_cost: Decimal
    final_tokens_cost: Decimal
    timeout: int = 30


class PollWaveSpeedGenerationTaskSchema(PollDbGenerationTaskSchema):
    wavespeed_task_id: str
    result_url: str | None
