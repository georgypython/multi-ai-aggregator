from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel

from src.models.enums import ModelProvider


class ModelConfigDataSchema(BaseModel):
    request_provider_model_key: str
    size: str
    quality: str
    provider_cost: Decimal
    provider: ModelProvider


class ImageRequestDataSchema(ModelConfigDataSchema):
    user_id: UUID
    ai_model_id: UUID
    provider_model_key: str
    prompt: str
    model_token_price_id: UUID
    media_file_urls: list[str] | None = None
    min_charge_tokens: Decimal
    free_requests_limit: int = 0


class ImageGenerationCreateRequestSchema(BaseModel):
    prompt: str
    size: str | None = None
    quality: str | None = None
    media_file_ids: list[UUID] | None = None


class ImageModelDetailResponseSchema(BaseModel):
    id: UUID
    name: str
    provider_key: str
    provider: ModelProvider
    sizes: list[str]
    qualities: list[str]
    prices_usd: dict[str, dict[str, Decimal]]


class ImagePriceParamsSchema(BaseModel):
    sizes: list[str]
    qualities: list[str]


class ImageModelProfileResponseSchema(ImagePriceParamsSchema):
    id: UUID
    name: str
    provider_key: str
    provider: ModelProvider


class ImageModelRawPriceDataSchema(BaseModel):
    ai_model_id: UUID
    size: str
    quality: str
    usd_price: Decimal


class ImageModelRawDataSchema(BaseModel):
    size: str
    quality: str
    provider_cost: Decimal
    provider: ModelProvider
    image_edit_model_name: str | None = None


class ImageModelPriceResponseSchema(BaseModel):
    ai_model_id: UUID
    provider_key: str
    size: str
    quality: str
    tokens_price: Decimal
