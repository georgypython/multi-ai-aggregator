from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field
from uuid import UUID

from src.core.models.enums import (
    GenerationType,
    GenerationStatus,
    ModelProvider,
    LLMConfigurationType,
    ModelType,
)


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


class ModelConfigDataSchema(BaseModel):
    request_provider_model_key: str
    size: str
    quality: str
    provider_cost: float
    provider: ModelProvider


class ImageRequestDataSchema(ModelConfigDataSchema):
    user_id: UUID
    ai_model_id: UUID
    provider_model_key: str
    prompt: str
    media_file_urls: list[str] | None = None
    min_charge_tokens: float
    free_requests_limit: int = 0


class VideoModelConfigDataSchema(BaseModel):
    duration_seconds: int
    size: str
    provider_cost: float
    provider: ModelProvider


class VideoRequestDataSchema(VideoModelConfigDataSchema):
    user_id: UUID
    ai_model_id: UUID
    provider_model_key: str
    prompt: str
    media_file_id: UUID | None = None
    min_charge_tokens: float
    free_requests_limit: int = 0


class ImageGenerationCreateRequestSchema(BaseModel):
    model_id: UUID
    prompt: str
    size: str | None = None
    quality: str | None = None
    media_file_ids: list[UUID] | None = None


class VideoGenerationCreateRequestSchema(BaseModel):
    model_id: UUID
    prompt: str
    duration_seconds: int | None = None
    size: str | None = None
    media_file_id: UUID | None = None


class WavespeedGenerationResponseSchema(BaseModel):
    task_id: str
    model_key: str | None = None
    status: GenerationStatus
    result_url: str | None = None
    created_at: str | None = None
    error: str | None = None

class GenerationRequestSchema(BaseModel):
    user_id: UUID
    ai_model_id: UUID
    generation_type: GenerationType
    hold_amount: float
    free_requests_limit: int = 0


class GenerationResultSchema(BaseModel):
    user_id: UUID
    generation_id: UUID
    hold_amount: float
    provider_cost: float
    result_url: str | None = None


class GenerationFinishData(BaseModel):
    ai_model_id: UUID
    generation_id: UUID
    user_id: UUID
    generation_type: GenerationType
    hold_amount: float
    provider_cost: float
    provider_status: GenerationStatus
    result_url: str | None = None
    text: str | None = None


class LLMProviderResponseSchema(BaseModel):
    text: str
    model: str
    input_tokens: int
    output_tokens: int
    total_tokens: int
    provider_cost: float | None = None
    raw: dict[str, Any]


class GenerationResultResponseDataSchema(BaseModel):
    ai_model_id: UUID
    user_id: UUID
    generation_id: UUID
    tokens_cost: float
    status: GenerationStatus
    text: str | None = None


class ImageModelDetailResponseSchema(BaseModel):
    id: UUID
    name: str
    provider_key: str
    provider: ModelProvider
    sizes: list[str]
    qualities: list[str]
    prices_usd: dict[str, dict[str, float]]


class ImageModelPriceResponseSchema(BaseModel):
    ai_model_id: UUID
    provider_key: str
    size: str
    quality: str
    tokens_price: float


class VideoModelDetailResponseSchema(BaseModel):
    id: UUID
    name: str
    provider_key: str
    provider: ModelProvider
    durations_seconds: list[int]
    sizes: list[str]
    prices_usd_by_duration: dict[str, dict[str, float]]


class VideoModelPriceResponseSchema(BaseModel):
    ai_model_id: UUID
    provider_key: str
    duration_seconds: int
    size: str
    tokens_price: float


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


class UserBalanceResponseSchema(BaseModel):
    user_id: UUID
    telegram_id: int
    available_tokens: float
    hold_tokens: float


class UploadFileResponseSchema(BaseModel):
    media_file_id: UUID


class PollWaveSpeedGenerationTaskSchema(BaseModel):
    ai_model_id: UUID
    user_id: UUID
    generation_id: UUID
    generation_type: GenerationType
    hold_amount: float
    provider_cost: float
    wavespeed_task_id: str
    poll_interval_seconds: int = 5
    max_attempts: int = 120
    current_attempt: int = 1
    timeout: int = 30
    final_tokens_cost: float
    result_url: str | None


class MediaFileDbDataSchema(BaseModel):
    id: UUID
    user_id: UUID
    content_type: str
    size_bytes: int
    object_key: str
    expires_at: datetime


class UpdloadFileDataSchema(BaseModel):
    data: bytes
    file: MediaFileDbDataSchema