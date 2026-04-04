from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel

from src.models.enums import ModelProvider
from .generations import GenerationRequestSchema


class VideoRequestDataSchema(GenerationRequestSchema):
    duration_seconds: int
    provider_cost: Decimal
    provider: ModelProvider
    media_file_url: str | None = None
    provider_model_key: str


class VideoGenerationCreateRequestSchema(BaseModel):
    prompt: str
    duration_seconds: int | None = None
    media_file_id: UUID | None = None


class VideoModelDetailResponseSchema(BaseModel):
    id: UUID
    name: str
    provider_key: str
    provider: ModelProvider
    durations_seconds: list[int]
    prices_usd_by_duration: dict[str, Decimal]


class VideoPriceParamsSchema(BaseModel):
    durations_seconds: list[int]


class VideoModelProfileResponseSchema(VideoPriceParamsSchema):
    id: UUID
    name: str
    provider_key: str
    provider: ModelProvider


class VideoModelRawPriceDataSchema(BaseModel):
    ai_model_id: UUID
    duration_seconds: int
    usd_price: Decimal


class VideoModelRawDataSchema(BaseModel):
    duration_seconds: int
    provider_cost: Decimal
    provider: ModelProvider
    image_edit_model_name: str | None = None


class VideoModelPriceResponseSchema(BaseModel):
    ai_model_id: UUID
    provider_key: str
    duration_seconds: int
    tokens_price: Decimal
