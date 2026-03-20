from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel

from src.models.enums import ModelProvider


class VideoModelConfigDataSchema(BaseModel):
    duration_seconds: int
    size: str
    provider_cost: Decimal
    provider: ModelProvider


class VideoRequestDataSchema(VideoModelConfigDataSchema):
    user_id: UUID
    ai_model_id: UUID
    provider_model_key: str
    prompt: str
    model_token_price_id: UUID
    media_file_id: UUID | None = None
    min_charge_tokens: Decimal
    free_requests_limit: int = 0


class VideoGenerationCreateRequestSchema(BaseModel):
    prompt: str
    duration_seconds: int | None = None
    size: str | None = None
    media_file_id: UUID | None = None


class VideoModelDetailResponseSchema(BaseModel):
    id: UUID
    name: str
    provider_key: str
    provider: ModelProvider
    durations_seconds: list[int]
    sizes: list[str]
    prices_usd_by_duration: dict[str, dict[str, Decimal]]


class VideoPriceParamsSchema(BaseModel):
    durations_seconds: list[int]
    sizes: list[str]


class VideoModelProfileResponseSchema(VideoPriceParamsSchema):
    id: UUID
    name: str
    provider_key: str
    provider: ModelProvider


class VideoModelRawPriceDataSchema(BaseModel):
    ai_model_id: UUID
    duration_seconds: int
    size: str
    usd_price: Decimal


class VideoModelRawDataSchema(BaseModel):
    duration_seconds: int
    size: str
    provider_cost: Decimal
    provider: ModelProvider


class VideoModelPriceResponseSchema(BaseModel):
    ai_model_id: UUID
    provider_key: str
    duration_seconds: int
    size: str
    tokens_price: Decimal
